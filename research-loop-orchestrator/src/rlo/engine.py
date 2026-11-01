"""The step engine: runs a stage's steps in order, pauses at human gates, resumes where it stopped.

Every step records its progress in the state file after each model call or check, so a run
interrupted by a budget, a rate limit, a manual hand-off or a crash continues from the last
completed piece rather than from the top.
"""

from __future__ import annotations

import json
import random
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from . import logs
from .calls import CallLog
from .checks import compare_csv, copy_matching, copy_tree, file_diff, run_check, run_test_plan
from .config import StageConfig, Step
from .fingerprint import compare, fingerprint_outputs, load_snapshot, save_snapshot
from .gate import GateItem, parse, unanswered, write_gate_file
from .models.base import Finding, FindingResponse, Judge, Reviewer, ToolAgent
from .models.manual import NeedsHuman
from .state import StageState, Store, now_iso
from .tools import files_matching


@dataclass
class Roles:
    author: ToolAgent
    reviewer: Reviewer
    judge: Judge
    builder: ToolAgent
    planter: ToolAgent

    def agent(self, role: str) -> ToolAgent:
        return {"author": self.author, "builder": self.builder, "planter": self.planter}[role]

    def family(self, role: str) -> str:
        return getattr(getattr(self, role), "family", "not stated")


class Stopped(Exception):
    """A step could not finish (budget, failed check after fixes). The stage can be re-run."""


def git_head(target: Path) -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=target, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def collect_artifacts(root: Path, globs: list[str]) -> dict[str, str]:
    return {str(p.relative_to(root)): p.read_text(encoding="utf-8", errors="replace") for p in files_matching(root, globs)}


class Engine:
    def __init__(self, cfg: StageConfig, variable: str, roles: Roles, store: Store, calls: CallLog,
                 rng: random.Random | None = None):
        self.cfg = cfg
        self.variable = variable
        self.roles = roles
        self.store = store
        self.calls = calls
        self.rng = rng or random.Random()
        self.target = store.target
        self.st = store.load(cfg.name, variable)

    # ------------------------------------------------------------------ driving
    def run(self) -> StageState:
        st = self.st
        if st.status == "waiting_human":
            raise RuntimeError(f"{self.cfg.name}/{self.variable} is waiting at a human gate: {st.gate_file}. "
                               "Fill it in and run `rlo approve`.")
        if st.status == "done":
            raise RuntimeError(f"{self.cfg.name}/{self.variable} is already done; use `rlo reset` to run it again")
        if st.status == "stopped" and st.current_step in st.progress:
            st.progress[st.current_step].pop("attempt", None)
        st.touch("running")
        st.manual_file = None
        self.store.save(st)
        for step in self.cfg.steps:
            if step.name in st.steps_done:
                continue
            st.current_step = step.name
            self.store.save(st)
            try:
                outcome = self.run_step(step)
            except NeedsHuman as e:
                st.manual_file = str(e.bundle.relative_to(self.target))
                st.touch("waiting_manual")
                self.store.save(st)
                return st
            except Stopped as e:
                st.notes.append(f"{step.name}: {e}")
                st.touch("stopped")
                self.store.save(st)
                return st
            if outcome == "paused":
                return st
            self._finish_step(step)
        st.touch("done")
        self.store.save(st)
        return st

    def _finish_step(self, step: Step) -> None:
        st = self.st
        if step.name not in st.steps_done:
            st.steps_done.append(step.name)
        st.progress.pop(step.name, None)
        self.store.save(st)

    def _progress(self, step: Step) -> dict:
        return self.st.progress.setdefault(step.name, {})

    def _context(self, step: Step, **extra) -> dict:
        ctx = {"stage": self.cfg.name, "variable": self.variable, "step": step.name, "round": 0}
        ctx.update(extra)
        return ctx

    def run_step(self, step: Step) -> str:
        return {"task": self.run_task_step, "check": self.run_check_step, "compare": self.run_compare_step,
                "planted_bugs": self.run_planted_bugs_step, "human": self.run_human_step,
                "snapshot": self.run_snapshot_step}[step.kind](step)

    # ------------------------------------------------------------------ task
    def _workdir(self, step: Step) -> Path:
        if not step.isolated:
            return self.target
        wd = self.store.work_dir / f"{self.cfg.name}_{self.variable}_{step.name}"
        if not wd.exists():
            wd.mkdir(parents=True)
            copy_matching(self.target, wd, step.inputs)
        return wd

    def run_task_step(self, step: Step) -> str:
        pr = self._progress(step)
        workdir = self._workdir(step)
        task = self.cfg.prompt_text(step.prompt, self.variable)
        agent = self.roles.agent(step.role)
        ctx = self._context(step, task=task)
        if pr.get("phase", "task") == "task":
            result = agent.run_task(task, workdir, ctx)
            self.store.write_round(self.st, f"{step.name}_task", asdict(result))
            if result.stopped_on_budget:
                raise Stopped("stopped on budget during the task")
            pr["phase"] = "review" if step.review else "collect"
            self.store.save(self.st)
        if pr["phase"] == "review":
            self._review_loop(step, workdir, agent, ctx)
            pr["phase"] = "collect"
            self.store.save(self.st)
        if step.isolated:
            copied = copy_matching(workdir, self.target, step.outputs)
            pr["copied_back"] = copied
        if step.gate_items_file:
            self._collect_gate_items(step)
        self._log_run(step, kind=f"task:{step.name}", checks={"review": pr.get("review", {}).get("summary", {})})
        return "done"

    def _collect_gate_items(self, step: Step) -> None:
        p = self.target / step.gate_items_file
        if not p.exists():
            raise Stopped(f"the {step.role} was asked to write {step.gate_items_file} but it does not exist")
        data = json.loads(p.read_text(encoding="utf-8"))
        for d in data["choices"]:
            item = GateItem.from_choice_dict(d, source=step.role)
            self._add_pending(item)

    def _add_pending(self, item: GateItem) -> None:
        ids = {d["id"] for d in self.st.pending_gate_items}
        if item.id in ids:
            item.id = f"{item.id}-{len(ids) + 1}"
        self.st.pending_gate_items.append(asdict(item))

    # ------------------------------------------------------------------ review loop
    def _review_loop(self, step: Step, workdir: Path, agent: ToolAgent, ctx: dict) -> None:
        pr = self._progress(step)
        rv = pr.setdefault("review", {"round": 0, "rejected": [], "findings": {}, "responses": {}, "resolutions": {}})
        reviewer = self.roles.reviewer
        while rv["round"] < self.cfg.review_rounds:
            rnd = rv["round"] + 1
            ctx["round"] = rnd
            if rnd > 1 and not rv["rejected"]:
                break
            fkey = f"r{rnd}_findings"
            if fkey not in rv:
                artifacts = collect_artifacts(workdir, step.outputs + self._definition_globs())
                if rnd == 1:
                    findings = reviewer.review(artifacts, ctx)
                else:
                    rejected = [(Finding.from_dict(rv["findings"][i]), FindingResponse(**rv["responses"][i])) for i in rv["rejected"]]
                    findings = reviewer.rereview(artifacts, rejected, ctx)
                rv[fkey] = [asdict(f) for f in findings]
                for f in findings:
                    rv["findings"][f.id] = asdict(f)
                self.store.write_round(self.st, f"{step.name}_review_r{rnd}", rv[fkey])
                self.store.save(self.st)
            findings = [Finding.from_dict(d) for d in rv[fkey]]
            if not findings:
                rv["rejected"] = []
                rv["round"] = rnd
                self.store.save(self.st)
                break
            rkey = f"r{rnd}_responses"
            if rkey not in rv:
                res = agent.respond(findings, workdir, ctx)
                if res.stopped_on_budget:
                    raise Stopped(f"stopped on budget while answering review round {rnd}")
                by_id = {x.id: x for x in res.responses}
                missing = [f.id for f in findings if f.id not in by_id]
                if missing:
                    raise Stopped(f"the {step.role} did not answer findings {missing}")
                rv[rkey] = [asdict(x) for x in res.responses]
                for x in res.responses:
                    rv["responses"][x.id] = asdict(x)
                self.store.write_round(self.st, f"{step.name}_respond_r{rnd}", asdict(res))
            by_id = {x["id"]: x for x in rv[rkey]}
            rv["rejected"] = [f.id for f in findings if by_id[f.id]["verdict"] == "reject"]
            rv["round"] = rnd
            self.store.save(self.st)
        if not rv.get("resolved"):
            self._resolve(step, workdir, agent, ctx, rv)
            rv["resolved"] = True
            self.store.save(self.st)
        rv["summary"] = {
            "findings_total": len(rv["findings"]),
            "accepted": sum(1 for r in rv["responses"].values() if r["verdict"] == "accept"),
            "disputed_after_rounds": len(rv["rejected"]),
            "routes": {k: v["route"] for k, v in rv["resolutions"].items()},
            "outcomes": {k: v["outcome"] for k, v in rv["resolutions"].items()},
        }
        self.store.save(self.st)

    @staticmethod
    def route_for(finding: Finding) -> str:
        if finding.kind == "error" and finding.checkable_by in ("test", "rule"):
            return "test"
        if finding.kind == "judgment":
            return "human"
        return "judge"

    def _resolve(self, step: Step, workdir: Path, agent: ToolAgent, ctx: dict, rv: dict) -> None:
        reviewer, judge = self.roles.reviewer, self.roles.judge
        ctx["round"] = self.cfg.review_rounds + 1
        for fid in rv["rejected"]:
            if fid in rv["resolutions"]:
                continue
            finding = Finding.from_dict(rv["findings"][fid])
            response = FindingResponse(**rv["responses"][fid])
            route = self.route_for(finding)
            res = {"route": route, "outcome": "pending_human", "detail": {}}
            if route == "test":
                plan = agent.plan_test(finding, workdir, ctx)
                if plan is None:
                    route = res["route"] = "judge"
                else:
                    try:
                        diff = file_diff(workdir, plan.subject, plan.mutant)
                    except FileNotFoundError as e:
                        diff = f"(missing file: {e})"
                    confirmed, why = reviewer.confirm_mutant(finding, diff, ctx)
                    out = run_test_plan(workdir, plan, confirmed)
                    res["detail"] = {"test": asdict(out), "reviewer_reason": why, "diff": diff[:4000]}
                    if out.valid:
                        res["outcome"] = "author" if out.subject_passed else "reviewer"
                    else:
                        res["route"] = "human"
                        res["detail"]["why_human"] = ("test did not fail on the mutant" if not out.mutant_failed
                                                      else "reviewer did not confirm the mutant carries its claim")
            if route == "judge":
                author_pos = response.reason
                reviewer_pos = f"{finding.claim}\nEvidence: {finding.evidence}\nProposed fix: {finding.proposed_fix}"
                a_is_author = self.rng.random() < 0.5
                pa, pb = (author_pos, reviewer_pos) if a_is_author else (reviewer_pos, author_pos)
                v = judge.judge(finding, pa, pb, ctx)
                v.sided_with = "author" if ((v.winner == "A") == a_is_author) else "reviewer"
                res["outcome"] = v.sided_with
                res["detail"] = {"verdict": asdict(v), "a_was_author": a_is_author}
            if res["route"] == "human":
                self._add_pending(GateItem(
                    id=f"DISPUTE-{fid}", item=finding.claim, options=["author", "reviewer", "other"],
                    reason=res["detail"].get("why_human", finding.evidence), source="dispute",
                    positions={"author": response.reason, "reviewer": finding.proposed_fix}))
            rv["resolutions"][fid] = res
            logs.log_dispute(self.store, stage=self.cfg.name, variable=self.variable, finding=asdict(finding),
                             author_response=asdict(response), route=res["route"], outcome=res["outcome"],
                             judge_family=self.roles.family("judge") if res["route"] == "judge" else None,
                             author_family=self.roles.family(step.role) if res["route"] == "judge" else None,
                             detail=res["detail"])
            self.store.save(self.st)
        must_fix = [Finding.from_dict(rv["findings"][k]) for k, v in rv["resolutions"].items() if v["outcome"] == "reviewer"]
        if must_fix and "fix" not in rv:
            ctx["phase"] = "fix"
            fix = agent.respond(must_fix, workdir, ctx)
            ctx.pop("phase")
            if fix.stopped_on_budget:
                raise Stopped("stopped on budget while applying settled findings")
            rv["fix"] = asdict(fix)
            self.store.write_round(self.st, f"{step.name}_fix_after_resolution", rv["fix"])
            for x in fix.responses:
                if x.verdict == "reject":
                    f = Finding.from_dict(rv["findings"][x.id])
                    self._add_pending(GateItem(
                        id=f"ESCALATED-{x.id}", item=f.claim, options=["author", "reviewer", "other"],
                        reason="a coded test or the judge sided with the reviewer, but the author still rejected",
                        source="dispute", positions={"author": x.reason, "reviewer": f.proposed_fix}))
                    self.st.notes.append(f"{step.name}: author rejected settled finding {x.id}; escalated to the gate")
            self.store.save(self.st)

    # ------------------------------------------------------------------ check / compare
    def _fix_with_author(self, step: Step, report: str, attempt: int) -> None:
        task = (f"The coded check `{step.name}` failed (attempt {attempt}). Diagnose the root cause first, then fix the "
                f"code or the definition it tests, never the check itself to make it pass. Do not skip, weaken or "
                f"delete a test.\n\nCHECK OUTPUT\n{report}")
        ctx = self._context(step, task=task, check_fix_for=step.name, round=attempt)
        res = self.roles.author.run_task(task, self.target, ctx)
        self.store.write_round(self.st, f"{step.name}_fix_{attempt}", asdict(res))
        if res.stopped_on_budget:
            raise Stopped("stopped on budget while fixing a failed check")

    def _check_once(self, step: Step, workdir: Path) -> dict:
        if step.kind == "compare":
            key = step.key
            if not key:
                kp = workdir / step.key_from
                if not kp.exists():
                    return {"ok": False, "error": f"key file missing: {step.key_from}"}
                key = json.loads(kp.read_text(encoding="utf-8"))["key"]
            res = compare_csv(workdir / step.left, workdir / step.right, key, step.tolerance)
            (self.store.report_dir / f"compare_{self.variable}_{step.name}.json").write_text(
                json.dumps(res, indent=2), encoding="utf-8")
            return res
        return run_check(workdir, step.command)

    def _run_check_like(self, step: Step) -> str:
        pr = self._progress(step)
        attempt = pr.get("attempt", 0)
        while True:
            res = self._check_once(step, self.target)
            summary = {k: v for k, v in res.items() if k not in ("stdout", "mismatches", "only_left", "only_right")}
            self._log_run(step, kind=f"{step.kind}:{step.name}", checks={"ok": res["ok"], "attempt": attempt, **summary})
            if res["ok"]:
                return "done"
            if attempt >= step.fix_rounds:
                raise Stopped(f"check still failing after {attempt} fix attempts; fix by hand and run again")
            attempt += 1
            pr["attempt"] = attempt
            self.store.save(self.st)
            self._fix_with_author(step, json.dumps(res, indent=2)[:12000], attempt)

    def run_check_step(self, step: Step) -> str:
        return self._run_check_like(step)

    def run_compare_step(self, step: Step) -> str:
        return self._run_check_like(step)

    # ------------------------------------------------------------------ planted bugs
    def run_planted_bugs_step(self, step: Step) -> str:
        pr = self._progress(step)
        bugs_path = self.target / step.bugs_file
        phase = pr.get("phase", "draft")
        if phase == "draft":
            if not bugs_path.exists():
                self._draft_bugs(step)
            data = json.loads(bugs_path.read_text(encoding="utf-8"))
            if not data.get("approved_by"):
                self._add_pending(GateItem(
                    id=f"PLANTED-BUGS-{step.name}", item=f"Approve the planted bug list in {step.bugs_file}",
                    options=["approve", "revise"], reason=f"{len(data.get('bugs', []))} bugs proposed; the list is drawn "
                    "from the error log and its classes and written by a model that is not this batch's reviewer",
                    source="system"))
                pr["phase"] = "await_approval"
                self.store.save(self.st)
                return self._pause_with_gate(step, title=f"Approve planted bugs for {self.variable}")
            pr["phase"] = "run"
        if phase == "await_approval":
            choice = pr.get("gate_choices", {}).get(f"PLANTED-BUGS-{step.name}", "")
            if choice != "approve":
                raise Stopped("planted bug list not approved; edit the list, then run again")
            data = json.loads(bugs_path.read_text(encoding="utf-8"))
            if not data.get("approved_by"):
                data["approved_by"] = pr.get("approved_by", "human")
                bugs_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            pr["phase"] = "run"
            self.store.save(self.st)
        data = json.loads(bugs_path.read_text(encoding="utf-8"))
        results = pr.setdefault("results", {})
        for bug in data["bugs"]:
            if bug["id"] in results:
                continue
            results[bug["id"]] = self._run_one_bug(step, bug)
            self.store.save(self.st)
        escaped = [b for b in data["bugs"] if not any(results[b["id"]]["caught"].values())]
        if escaped and not pr.get("escaped_fix_done"):
            task = ("These planted bugs got past every check layer. For each one, add or fix a check in the repository "
                    "so it would be caught, then stop. Do not touch the mutated copies.\n\n" + json.dumps(escaped, indent=2))
            res = self.roles.author.run_task(task, self.target, self._context(step, task=task, check_fix_for=step.name))
            self.store.write_round(self.st, f"{step.name}_escaped_fix", asdict(res))
            pr["escaped_fix_done"] = True
            for b in escaped:
                results[b["id"]] = self._run_one_bug(step, b)
            self.store.save(self.st)
            escaped = [b for b in data["bugs"] if not any(results[b["id"]]["caught"].values())]
        for b in escaped:
            self._add_pending(GateItem(id=f"ESCAPED-{b['id']}", item=f"Planted bug {b['id']} escaped every layer: {b['description']}",
                                       options=["add check by hand", "accept the risk"], reason="a check was added by the author and the bug still escaped",
                                       source="check"))
        self._write_catch_matrix(step, data["bugs"], results)
        self._log_run(step, kind=f"planted_bugs:{step.name}",
                      checks={"bugs": len(data["bugs"]), "escaped": len(escaped), "layers": step.layers})
        return "done"

    def _draft_bugs(self, step: Step) -> None:
        errors = self.store.read_jsonl("error_log.jsonl")
        classes = ["upstream in another file", "spread across files", "visible only in the data", "allowed by an unclear definition"]
        task = (f"Draft a list of realistic planted bugs for the variable `{self.variable}`, to test whether the checks "
                f"catch them. Draw them from the error log entries below (the kinds that actually got through) and from "
                f"these classes: {classes}. Each bug must be plantable in files matching {step.mutable}. Write "
                f"{step.bugs_file} as {{\"bugs\": [{{\"id\": \"B1\", \"class\": \"...\", \"description\": \"...\", "
                f"\"where\": \"file\", \"source\": \"error log id or class\"}}], \"approved_by\": \"\"}}. Six to twelve "
                f"bugs. Do not plant anything yet.\n\nERROR LOG\n{json.dumps(errors, indent=2)[:12000]}")
        res = self.roles.planter.run_task(task, self.target, self._context(step, task=task))
        self.store.write_round(self.st, f"{step.name}_draft", asdict(res))
        if not (self.target / step.bugs_file).exists():
            raise Stopped(f"the planter did not write {step.bugs_file}")

    def _run_one_bug(self, step: Step, bug: dict) -> dict:
        work = self.store.work_dir / f"mutant_{self.cfg.name}_{self.variable}_{bug['id']}"
        copy_tree(self.target, work, step.copy_exclude)
        task = (f"Plant exactly this bug in the work folder, changing only files matching {step.mutable}. Make it look "
                f"like an honest mistake: no comments or names that give it away. Then stop.\n\n{json.dumps(bug, indent=2)}")
        ctx = self._context(step, task=task, round=0, bug=bug["id"])
        res = self.roles.planter.run_task(task, work, ctx)
        changed = []
        for p in files_matching(work, step.mutable):
            rel = p.relative_to(work)
            orig = self.target / rel
            if not orig.exists() or orig.read_bytes() != p.read_bytes():
                changed.append(str(rel))
        caught: dict[str, bool] = {}
        detail: dict[str, dict] = {}
        if step.rebuild:
            rb = run_check(work, step.rebuild)
            detail["rebuild"] = {"ok": rb["ok"], "returncode": rb["returncode"], "stderr": rb["stderr"][-500:]}
        for layer in step.layers:
            if layer == "ai_review":
                arts = collect_artifacts(work, step.mutable + [s for s in self._definition_globs()])
                findings = self.roles.reviewer.review(arts, {**ctx, "task": "Compare the build against the definition and report every deviation."})
                hits = [f for f in findings if f.kind == "error" and any(c in f.evidence or c in f.claim for c in changed)]
                caught[layer] = bool(hits)
                detail[layer] = {"findings": [asdict(f) for f in findings], "note": "caught = an error finding names a changed file; confirm by hand"}
                continue
            ls = self.cfg.step(layer)
            r = self._check_once(ls, work)
            caught[layer] = not r["ok"]
            detail[layer] = {k: v for k, v in r.items() if k in ("ok", "returncode", "n_mismatches", "n_only_left", "n_only_right", "error")}
        return {"files_changed": changed, "planter_summary": res.summary, "caught": caught, "detail": detail}

    def _definition_globs(self) -> list[str]:
        return [f"spec/{self.variable}_definition.md", "spec/*definition*.md"]

    def _write_catch_matrix(self, step: Step, bugs: list[dict], results: dict) -> None:
        layers = step.layers
        lines = [f"# Catch matrix: {self.variable} ({self.cfg.name}/{step.name})", "", f"Written: {now_iso()}", "",
                 "| Bug | Class | " + " | ".join(layers) + " | Caught by |", "|---|---|" + "---|" * len(layers) + "---|"]
        for b in bugs:
            r = results[b["id"]]
            marks = ["yes" if r["caught"].get(l) else "no" for l in layers]
            n = sum(1 for m in marks if m == "yes")
            lines.append(f"| {b['id']} | {b.get('class','')} | " + " | ".join(marks) + f" | {n} |")
        per_layer = {l: sum(1 for b in bugs if results[b['id']]['caught'].get(l)) for l in layers}
        lines += ["", "Per layer: " + ", ".join(f"{l} {per_layer[l]}/{len(bugs)}" for l in layers),
                  "", "Escaped: " + (", ".join(b['id'] for b in bugs if not any(results[b['id']]['caught'].values())) or "none"),
                  "", "The ai_review column marks a bug caught when an error finding names a changed file; confirm by hand."]
        (self.store.report_dir / f"catch_matrix_{self.variable}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (self.store.report_dir / f"catch_matrix_{self.variable}.json").write_text(
            json.dumps({"bugs": bugs, "results": results, "layers": layers}, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------ human gate
    def _pause_with_gate(self, step: Step, title: str | None = None) -> str:
        items = [GateItem(**d) for d in self.st.pending_gate_items]
        for extra in step.items_from:
            p = self.target / extra
            if p.exists():
                for d in json.loads(p.read_text(encoding="utf-8"))["choices"]:
                    items.append(GateItem.from_choice_dict(d, source="author"))
        if step.recycle_rule:
            prior = [d for d in self.store.read_jsonl("decision_log.jsonl")
                     if d.get("variable") == self.variable and d.get("gate_item_id", "").startswith("CALL") and d.get("choice") == "recycle"]
            if len(prior) >= 2:
                items.append(GateItem(id=f"KILL-REVIEW-{step.name}", item=f"House rule: {len(prior)} recycles already on this claim; a kill review is mandatory",
                                      options=["kill", "continue with written justification"], reason="two recycles per core claim, then a mandatory kill review",
                                      source="system"))
        if step.kind == "human":
            items.append(GateItem(id=f"SIGNOFF-{step.name}", item=step.title or f"Sign off {step.name}",
                                  options=["approve", "stop"], reason="your explicit sign-off closes this gate", source="system"))
        gate_path = self.store.gates_dir / f"{self.cfg.name}_{self.variable}_{step.name}.md"
        write_gate_file(gate_path, items, gate_no=self.cfg.gate_no, title=title or step.title or self.cfg.title,
                        stage=self.cfg.name, variable=self.variable, when=now_iso())
        self.st.gate_file = str(gate_path.relative_to(self.target))
        self.st.touch("waiting_human")
        self.store.save(self.st)
        return "paused"

    def run_human_step(self, step: Step) -> str:
        pr = self._progress(step)
        if pr.get("approved"):
            return "done"
        return self._pause_with_gate(step)

    # ------------------------------------------------------------------ snapshot
    def run_snapshot_step(self, step: Step) -> str:
        fp = fingerprint_outputs(self.target, step.include)
        snap = self.store.snapshots_dir / f"{self.cfg.name}_{self.variable}.json"
        before = load_snapshot(snap)
        if before is None:
            save_snapshot(snap, fp, {"stage": self.cfg.name, "variable": self.variable, "saved": now_iso(),
                                     "include": step.include})
            self._log_run(step, kind="snapshot", checks={"first_snapshot": True, "files": len(fp)})
            return "done"
        diff = compare(before, fp)
        logs.log_change(self.store, what=f"{self.cfg.name}/{self.variable} re-run", cls="tooling" if diff["identical"] else "unclassified",
                        reason="outputs re-fingerprinted at the snapshot step", before_results=True,
                        fingerprints_identical=diff["identical"], approved_by="auto (sign-off rule)" if diff["identical"] else "waiting")
        if diff["identical"]:
            save_snapshot(snap, fp, {"stage": self.cfg.name, "variable": self.variable, "saved": now_iso(), "include": step.include})
        else:
            self._add_pending(GateItem(id=f"SNAPSHOT-{step.name}", item="Outputs changed since the approved snapshot",
                                       options=["approve new snapshot", "reject"], reason=json.dumps(diff), source="system"))
            self.st.notes.append(f"{step.name}: fingerprints moved: {diff}")
        self._log_run(step, kind="snapshot", checks={"identical": diff["identical"], **{k: len(v) for k, v in diff.items() if isinstance(v, list)}})
        return "done"

    # ------------------------------------------------------------------ run log
    def _log_run(self, step: Step, kind: str, checks: dict) -> None:
        outs = fingerprint_outputs(self.target, step.outputs or step.include)
        ins = fingerprint_outputs(self.target, step.inputs)
        logs.log_run(self.store, stage=self.cfg.name, variable=self.variable, kind=kind, git_commit=git_head(self.target),
                     inputs=ins, outputs=outs, settings={"models": {r: self.cfg.model(r) for r in ("author", "reviewer", "judge", "builder", "planter")},
                                                        "review_rounds": self.cfg.review_rounds, "step": step.name},
                     checks=checks)


def approve_stage(*, cfg: StageConfig, store: Store, variable: str, decided_by: str) -> dict:
    """Read the filled-in checklist, log every decision, and clear the gate so `run` can continue."""
    st = store.load(cfg.name, variable)
    if st.status != "waiting_human" or not st.gate_file:
        raise RuntimeError(f"{cfg.name}/{variable} is not waiting at a gate (status {st.status})")
    items = parse((store.target / st.gate_file).read_text(encoding="utf-8"))
    missing = unanswered(items)
    if missing:
        raise RuntimeError("these items still have an empty Choice: " + ", ".join(missing))
    off_list = [it.id for it in items if it.options and it.choice not in it.options and it.choice.lower() != "other"]
    decisions = [logs.log_decision(store, it, stage=cfg.name, variable=variable, decided_by=decided_by) for it in items]
    judgment = logs.log_judgment(store, gate=cfg.gate_no, stage=cfg.name, variable=variable, decisions=decisions, decided_by=decided_by)
    step = cfg.step(st.current_step)
    pr = st.progress.setdefault(step.name, {})
    pr["gate_choices"] = {it.id: it.choice for it in items}
    pr["approved_by"] = decided_by
    st.pending_gate_items = []
    st.gate_file = None
    stop = any(it.id.startswith("SIGNOFF-") and it.choice == "stop" for it in items)
    if step.kind == "human":
        pr["approved"] = True
        st.steps_done.append(step.name)
        st.progress.pop(step.name, None)
    st.notes.append(f"gate {cfg.gate_no} at {step.name} approved by {decided_by}: "
                    f"{judgment['accepted_default']} defaults kept, {judgment['overruled_default']} overruled, {judgment['chose']} chosen")
    st.touch("stopped" if stop else "running")
    if not stop and all(s.name in st.steps_done for s in cfg.steps):
        st.touch("done")
    store.save(st)
    return {"decisions": decisions, "judgment": judgment, "off_list": off_list, "stopped": stop, "status": st.status}
