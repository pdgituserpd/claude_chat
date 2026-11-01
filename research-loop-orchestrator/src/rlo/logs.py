"""Log entries, built by the program from its own records (gate files, call files, check output).

Formats follow the process document. Entries are JSON lines under logs/ in the target repo.
"""

from __future__ import annotations

import platform
import subprocess
import sys

from . import __version__
from .gate import GateItem
from .state import Store, now_iso

ERROR_TYPES = ("data", "measurement", "estimation", "reporting", "literature")
FOUND_BY = ("Pouya", "same model", "another model", "coded check")
CHANGE_CLASSES = ("correction", "validity_repair", "choice", "exploratory", "theory", "tooling", "unclassified")
CALLS = ("go", "recycle", "hold", "kill")


def next_id(store: Store, filename: str, prefix: str) -> str:
    """Unique, monotone ids. Reads the latest log before adding one."""
    nums = []
    for e in store.read_jsonl(filename):
        i = str(e.get("id", ""))
        if i.startswith(prefix) and i[len(prefix):].isdigit():
            nums.append(int(i[len(prefix):]))
    return f"{prefix}{(max(nums) + 1) if nums else 1:03d}"


def _version_of(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        out = (r.stdout or r.stderr).strip().splitlines()
        return out[0][:120] if out else "not stated"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return "not stated"


def software_versions(extra: dict | None = None) -> dict:
    v = {
        "rlo": __version__,
        "python": sys.version.split()[0],
        "os": f"{platform.system()} {platform.release()}",
        "R": _version_of(["Rscript", "--version"]),
    }
    if extra:
        v.update(extra)
    return v


def log_decision(store: Store, it: GateItem, *, stage: str, variable: str, decided_by: str) -> dict:
    rec = {
        "id": next_id(store, "decision_log.jsonl", "D"), "date": now_iso(), "stage": stage, "variable": variable,
        "item": it.item, "gate_item_id": it.id, "source": it.source, "options": it.options,
        "precedent": it.precedent or "not stated", "precedent_type": it.precedent_type,
        "ai_default": it.shown_default() or None, "choice": it.choice, "outcome": it.outcome(),
        "reason": it.note or "not stated", "decided_by": decided_by, "status": "decided",
    }
    store.append_jsonl("decision_log.jsonl", rec)
    return rec


def log_judgment(store: Store, *, gate: int, stage: str, variable: str, decisions: list[dict], decided_by: str,
                 literature: str = "not stated") -> dict:
    counts = {k: sum(1 for d in decisions if d["outcome"] == k) for k in ("accepted_default", "overruled_default", "chose")}
    with_default = counts["accepted_default"] + counts["overruled_default"]
    rec = {
        "id": next_id(store, "judgment_log.jsonl", "J"), "date": now_iso(), "gate": gate, "stage": stage,
        "variable": variable, "items": len(decisions), **counts,
        "overrule_rate": (counts["overruled_default"] / with_default) if with_default else None,
        "decision_ids": [d["id"] for d in decisions], "literature_basis": literature, "decided_by": decided_by,
    }
    store.append_jsonl("judgment_log.jsonl", rec)
    return rec


def log_change(store: Store, *, what: str, cls: str, reason: str, before_results: bool,
               fingerprints_identical: bool, approved_by: str) -> dict:
    if cls not in CHANGE_CLASSES:
        raise ValueError(f"change class must be one of {CHANGE_CLASSES}")
    rec = {
        "id": next_id(store, "change_log.jsonl", "C"), "date": now_iso(), "what": what, "class": cls, "reason": reason,
        "before_results_seen": before_results, "would_make_either_way": "not stated", "can_test_still_fail": "not stated",
        "fingerprints_identical": fingerprints_identical, "approved_by": approved_by,
        "status": "auto_signed_off" if fingerprints_identical else "waiting_human",
    }
    store.append_jsonl("change_log.jsonl", rec)
    return rec


def log_run(store: Store, *, stage: str, variable: str, kind: str, git_commit: str, inputs: dict, outputs: dict,
            settings: dict, checks: dict, is_test: bool = False, versions: dict | None = None) -> dict:
    rec = {
        "id": next_id(store, "run_log.jsonl", "R"), "time": now_iso(), "stage": stage, "variable": variable,
        "kind": kind, "is_test_run": is_test, "git_commit": git_commit or "not stated",
        "software_versions": versions or software_versions(), "input_fingerprints": inputs,
        "output_fingerprints": outputs, "settings": settings, "checks": checks,
    }
    store.append_jsonl("run_log.jsonl", rec)
    return rec


def log_dispute(store: Store, *, stage: str, variable: str, finding: dict, author_response: dict, route: str,
                outcome: str, judge_family: str | None, author_family: str | None, detail: dict) -> dict:
    rec = {
        "id": next_id(store, "dispute_log.jsonl", "X"), "date": now_iso(), "stage": stage, "variable": variable,
        "finding": finding, "author_response": author_response, "route": route, "outcome": outcome,
        "judge_family": judge_family, "author_family": author_family,
        "judge_sided_with_own_family": ((outcome == "author") == (judge_family == author_family))
        if route == "judge" and judge_family and author_family else None,
        "detail": detail,
    }
    store.append_jsonl("dispute_log.jsonl", rec)
    return rec


def log_error(store: Store, *, type_: str, produced_by: str, how_found: str, found_by: str, how_far: str,
              effect: str, confirmed_by_rerun: bool, fix: str, check_added: str, silent: bool, wrong: bool,
              in_research: bool, variable: str = "", stage: str = "", in_development: bool = False) -> dict:
    """Silent errors only. The three tests must all be yes or the entry is refused."""
    if type_ not in ERROR_TYPES:
        raise ValueError(f"type must be one of {ERROR_TYPES}")
    if found_by not in FOUND_BY:
        raise ValueError(f"found_by must be one of {FOUND_BY}")
    failed = [n for n, ok in (("silent", silent), ("wrong", wrong), ("in_research", in_research)) if not ok]
    if failed:
        raise ValueError("not an error-log entry; failed test(s): " + ", ".join(failed))
    rec = {
        "id": next_id(store, "error_log.jsonl", "E"), "date": now_iso(), "type": type_, "variable": variable,
        "stage": stage, "produced_by": produced_by or "not stated", "how_found": how_found, "found_by": found_by,
        "how_far_it_got": how_far, "effect": effect, "confirmed_by_rerun": confirmed_by_rerun, "fix": fix,
        "check_added": check_added or "not stated", "in_development": in_development,
    }
    store.append_jsonl("error_log.jsonl", rec)
    return rec


def log_stop(store: Store, *, paper: str, call: str, reason: str, decided_by: str) -> dict:
    if call not in ("shelved", "killed"):
        raise ValueError("call must be shelved or killed; shelved is not dead")
    rec = {"id": next_id(store, "stopped_papers_log.jsonl", "S"), "date": now_iso(), "paper": paper, "call": call,
           "reason": reason, "decided_by": decided_by}
    store.append_jsonl("stopped_papers_log.jsonl", rec)
    return rec


def counts(store: Store) -> dict:
    snaps = list(store.snapshots_dir.glob("*.json"))
    runs = store.read_jsonl("run_log.jsonl")
    errors = store.read_jsonl("error_log.jsonl")
    audited_errors = [e for e in errors if not e.get("in_development")]
    stops = store.read_jsonl("stopped_papers_log.jsonl")
    disputes = store.read_jsonl("dispute_log.jsonl")
    judged = [d for d in disputes if d["route"] == "judge" and d.get("judge_sided_with_own_family") is not None]
    judg = store.read_jsonl("judgment_log.jsonl")
    with_default = sum(j.get("accepted_default", 0) + j.get("overruled_default", 0) for j in judg)
    overruled = sum(j.get("overruled_default", 0) for j in judg)
    return {
        "variables_with_approved_snapshot": len(snaps),
        "runs": len(runs),
        "test_runs": sum(1 for r in runs if r.get("is_test_run")),
        "silent_errors": len(errors),
        "silent_errors_in_audited_work": len(audited_errors),
        "errors_per_run": (len(audited_errors) / len(runs)) if runs else None,
        "stopped_papers": len(stops),
        "disputes": len(disputes),
        "judge_own_family_rate": (sum(1 for d in judged if d["judge_sided_with_own_family"]) / len(judged)) if judged else None,
        "gate_items_with_default": with_default,
        "default_overrule_rate": (overruled / with_default) if with_default else None,
    }
