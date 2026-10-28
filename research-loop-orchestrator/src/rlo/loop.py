"""The stage loop: author -> review -> respond -> re-review -> resolve -> gate.

run_stage() drives one stage for one variable in one target repository. It stops at a
human gate by writing a checklist and setting state to waiting_human. approve_stage()
reads the checklist back, writes the logs, and marks the stage done.
"""

from __future__ import annotations

import json
import random
import subprocess
from dataclasses import asdict
from pathlib import Path

from . import logs
from .calls import CallLog
from .config import StageConfig
from .fingerprint import compare, fingerprint_outputs, load_snapshot, save_snapshot
from .gate import GateItem, parse, unanswered, write_gate_file
from .models.base import Author, Finding, FindingResponse, Judge, Reviewer
from .resolve import resolve
from .state import StageState, Store, now_iso


def git_head(target: Path) -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=target, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def collect_artifacts(target: Path, globs: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for g in globs:
        for p in sorted(Path(target).glob(g)):
            if p.is_file() and ".git" not in p.parts and ".rlo" not in p.parts:
                out[str(p.relative_to(target))] = p.read_text(encoding="utf-8", errors="replace")
    return out


def _gate_items_from_author(target: Path, cfg: StageConfig) -> list[GateItem]:
    if not cfg.gate_items_file:
        return []
    p = Path(target) / cfg.gate_items_file
    if not p.exists():
        raise FileNotFoundError(
            f"the author was asked to write {cfg.gate_items_file} but it does not exist; the stage cannot gate"
        )
    data = json.loads(p.read_text(encoding="utf-8"))
    items = []
    for d in data["choices"]:
        items.append(GateItem(
            id=d["id"], item=d["item"], options=list(d["options"]), default=d.get("default", ""),
            precedent=d.get("precedent", ""), reason=d.get("reason", ""), source="author",
        ))
    return items


def run_stage(
    *,
    cfg: StageConfig,
    target: Path,
    variable: str,
    author: Author,
    reviewer: Reviewer,
    judge: Judge,
    store: Store,
    calls: CallLog,
    author_family: str = "anthropic",
    judge_family: str = "anthropic",
    rng: random.Random | None = None,
) -> StageState:
    target = Path(target)
    st = store.load(cfg.name, variable)
    if st.status == "waiting_human":
        raise RuntimeError(f"stage {cfg.name}/{variable} is waiting at a human gate: {st.gate_file}")
    if st.status == "done":
        raise RuntimeError(f"stage {cfg.name}/{variable} is already done; use a new variable name or reset")

    context = {"stage": cfg.name, "variable": variable, "round": 0}
    task = cfg.prompt_text("author").replace("{{variable}}", variable)
    context["task"] = task
    inputs_fp = fingerprint_outputs(target, cfg.inputs)

    # 1. author
    st.touch("authoring")
    store.save(st)
    a = author.author(task, context)
    store.write_round(st, "author", asdict(a))
    if a.stopped_on_budget:
        st.notes.append("author stopped on budget before finishing")
        st.touch("stopped")
        store.save(st)
        return st

    # 2. review rounds
    all_findings: dict[str, Finding] = {}
    responses: dict[str, FindingResponse] = {}
    rejected: list[tuple[Finding, FindingResponse]] = []
    for rnd in range(1, cfg.review_rounds + 1):
        st.round = rnd
        context["round"] = rnd
        st.touch("reviewing")
        store.save(st)
        artifacts = collect_artifacts(target, cfg.outputs)
        if rnd == 1:
            findings = reviewer.review(artifacts, context)
        else:
            if not rejected:
                break
            findings = reviewer.rereview(artifacts, rejected, context)
        for f in findings:
            all_findings[f.id] = f
        store.write_round(st, f"review_r{rnd}", [asdict(f) for f in findings])
        if not findings:
            rejected = []
            break
        r = author.respond(findings, context)
        store.write_round(st, f"respond_r{rnd}", asdict(r))
        if r.stopped_on_budget:
            st.notes.append(f"author stopped on budget in round {rnd}")
            st.touch("stopped")
            store.save(st)
            return st
        by_id = {x.id: x for x in r.responses}
        missing = [f.id for f in findings if f.id not in by_id]
        if missing:
            raise RuntimeError(f"author did not answer findings {missing}")
        rejected = [(f, by_id[f.id]) for f in findings if by_id[f.id].verdict == "reject"]
        for f in findings:
            responses[f.id] = by_id[f.id]

    # 3. resolve what is still disputed
    st.touch("resolving")
    store.save(st)
    report = resolve(rejected, author, judge, context, rng=rng)
    store.write_round(st, "resolve", [
        {"finding": asdict(r.finding), "route": r.route, "outcome": r.outcome,
         "test": asdict(r.test) if r.test else None, "verdict": asdict(r.verdict) if r.verdict else None}
        for r in report.resolutions
    ])
    for r in report.resolutions:
        logs.log_dispute(
            store, stage=cfg.name, variable=variable, finding=asdict(r.finding),
            author_response=asdict(r.author_response), route=r.route, outcome=r.outcome,
            judge_family=judge_family if r.route == "judge" else None,
            author_family=author_family if r.route == "judge" else None,
            detail={"test": asdict(r.test) if r.test else None, "verdict": asdict(r.verdict) if r.verdict else None},
        )
    # A test or a judge that sided with the reviewer means the author must make the change.
    must_fix = [r.finding for r in report.resolutions if r.outcome == "reviewer"]
    still_rejected: list[str] = []
    if must_fix:
        context["round"] = cfg.review_rounds + 1
        context["phase"] = "fix"
        fix = author.respond(must_fix, context)
        context.pop("phase")
        store.write_round(st, "fix_after_resolution", asdict(fix))
        still_rejected = [x.id for x in fix.responses if x.verdict == "reject"]
        if still_rejected:
            st.notes.append(f"author rejected settled findings {still_rejected}; escalated to the gate")

    # 4. run log for the stage's build
    outputs_fp = fingerprint_outputs(target, cfg.outputs)
    logs.log_run(
        store, stage=cfg.name, variable=variable, kind="stage_build", git_commit=git_head(target),
        inputs=inputs_fp, outputs=outputs_fp,
        settings={"author_model": cfg.author_model, "reviewer_model": cfg.reviewer_model, "judge_model": cfg.judge_model,
                  "review_rounds": cfg.review_rounds},
        checks={"findings_total": len(all_findings), "accepted": sum(1 for x in responses.values() if x.verdict == "accept"),
                "disputed_after_rounds": len(rejected), "resolved_for_reviewer": len(must_fix)},
    )

    # 5. gate
    if cfg.gate == "human":
        items = _gate_items_from_author(target, cfg)
        for r in report.for_human():
            items.append(GateItem(
                id=f"DISPUTE-{r.finding.id}", item=r.finding.claim,
                options=["author", "reviewer", "other"], default="",
                precedent="", reason=r.finding.evidence, source="dispute",
                positions={"author": r.author_response.reason, "reviewer": r.finding.proposed_fix},
            ))
        if still_rejected:
            for fid in still_rejected:
                f = all_findings[fid]
                items.append(GateItem(
                    id=f"ESCALATED-{fid}", item=f.claim, options=["author", "reviewer", "other"], default="",
                    precedent="", reason="a coded test or the judge sided with the reviewer, but the author still rejected",
                    source="dispute", positions={"author": responses[fid].reason, "reviewer": f.proposed_fix},
                ))
        gate_path = store.gates_dir / f"{cfg.name}_{variable}.md"
        write_gate_file(gate_path, items, gate_no=_gate_number(cfg), title=cfg.title, stage=cfg.name,
                        variable=variable, when=now_iso())
        st.gate_file = str(gate_path.relative_to(store.target))
        st.touch("waiting_human")
    else:
        _snapshot_and_signoff(store, cfg, variable, outputs_fp)
        st.touch("done")
    store.save(st)
    return st


def _gate_number(cfg: StageConfig) -> int:
    for ch in cfg.name:
        if ch.isdigit():
            return int(ch)
    return 0


def _snapshot_and_signoff(store: Store, cfg: StageConfig, variable: str, outputs_fp: dict) -> dict:
    snap = store.snapshots_dir / f"{cfg.name}_{variable}.json"
    before = load_snapshot(snap)
    if before is None:
        save_snapshot(snap, outputs_fp, {"stage": cfg.name, "variable": variable, "saved": now_iso()})
        return {"identical": None, "first_snapshot": True}
    diff = compare(before, outputs_fp)
    logs.log_change(
        store, what=f"{cfg.name}/{variable} outputs re-run", cls="tooling" if diff["identical"] else "unclassified",
        reason="stage re-run", before_results=True, fingerprints_identical=diff["identical"],
        approved_by="auto (sign-off rule)" if diff["identical"] else "waiting",
    )
    if diff["identical"]:
        save_snapshot(snap, outputs_fp, {"stage": cfg.name, "variable": variable, "saved": now_iso()})
    return diff


def approve_stage(*, cfg: StageConfig, target: Path, variable: str, store: Store, decided_by: str) -> dict:
    st = store.load(cfg.name, variable)
    if st.status != "waiting_human" or not st.gate_file:
        raise RuntimeError(f"stage {cfg.name}/{variable} is not waiting at a gate (status {st.status})")
    gate_path = store.target / st.gate_file
    items = parse(gate_path.read_text(encoding="utf-8"))
    missing = unanswered(items)
    if missing:
        raise RuntimeError("these items still have an empty Choice: " + ", ".join(missing))
    bad = [it.id for it in items if it.options and it.choice not in it.options and it.choice.lower() != "other"]
    decisions = []
    for it in items:
        decisions.append(logs.log_decision(store, it, stage=cfg.name, variable=variable, decided_by=decided_by))
    overruled = [d for d in decisions if d["overruled_default"]]
    logs.log_judgment(
        store, gate=_gate_number(cfg), stage=cfg.name, variable=variable,
        proposed=f"{len(items)} items with AI defaults",
        chosen=f"{len(items) - len(overruled)} defaults kept, {len(overruled)} overruled",
        reason="see decision log entries " + ", ".join(d["id"] for d in decisions), decided_by=decided_by,
    )
    outputs_fp = fingerprint_outputs(target, cfg.outputs)
    snap = store.snapshots_dir / f"{cfg.name}_{variable}.json"
    save_snapshot(snap, outputs_fp, {"stage": cfg.name, "variable": variable, "approved_by": decided_by,
                                     "gate_file": st.gate_file, "saved": now_iso()})
    st.touch("done")
    st.notes.append(f"approved by {decided_by}; {len(overruled)} of {len(items)} defaults overruled")
    if bad:
        st.notes.append(f"choices outside the listed options (recorded as given): {bad}")
    store.save(st)
    return {"decisions": decisions, "overruled": len(overruled), "total": len(items), "off_list": bad}
