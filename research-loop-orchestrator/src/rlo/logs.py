"""Log entries, built from the records the program itself wrote (gate files, call files).

Formats follow the process document: decision log, judgment log, change log, run log.
Entries are JSON lines under logs/ in the target repo; `rlo status` renders them.
"""

from __future__ import annotations

from .gate import GateItem
from .state import Store, now_iso


def next_id(store: Store, filename: str, prefix: str) -> str:
    """Unique, monotone ids. Checks the latest log before adding one."""
    existing = store.read_jsonl(filename)
    nums = []
    for e in existing:
        i = str(e.get("id", ""))
        if i.startswith(prefix) and i[len(prefix):].isdigit():
            nums.append(int(i[len(prefix):]))
    return f"{prefix}{(max(nums) + 1) if nums else 1:03d}"


def log_decision(store: Store, it: GateItem, *, stage: str, variable: str, decided_by: str) -> dict:
    rec = {
        "id": next_id(store, "decision_log.jsonl", "D"),
        "date": now_iso(),
        "stage": stage,
        "variable": variable,
        "item": it.item,
        "gate_item_id": it.id,
        "options": it.options,
        "ai_default": it.default,
        "choice": it.choice,
        "overruled_default": (it.choice != it.default) if it.default else None,
        "reason": it.note or "not stated",
        "precedent": it.precedent or "not stated",
        "decided_by": decided_by,
        "status": "decided",
    }
    store.append_jsonl("decision_log.jsonl", rec)
    return rec


def log_judgment(store: Store, *, gate: int, stage: str, variable: str, proposed: str, chosen: str,
                 reason: str, decided_by: str, literature: str = "not stated") -> dict:
    rec = {
        "id": next_id(store, "judgment_log.jsonl", "J"),
        "date": now_iso(),
        "gate": gate,
        "stage": stage,
        "variable": variable,
        "ai_proposed": proposed,
        "human_chose": chosen,
        "overruled": proposed != chosen,
        "reason": reason or "not stated",
        "literature_basis": literature,
        "decided_by": decided_by,
    }
    store.append_jsonl("judgment_log.jsonl", rec)
    return rec


def log_change(store: Store, *, what: str, cls: str, reason: str, before_results: bool,
               fingerprints_identical: bool, approved_by: str) -> dict:
    rec = {
        "id": next_id(store, "change_log.jsonl", "C"),
        "date": now_iso(),
        "what": what,
        "class": cls,  # correction | validity_repair | choice | exploratory | theory | tooling
        "reason": reason,
        "before_results_seen": before_results,
        "would_make_either_way": "not stated",  # the human answers this one
        "can_test_still_fail": "not stated",
        "fingerprints_identical": fingerprints_identical,
        "approved_by": approved_by,
        "status": "auto_signed_off" if fingerprints_identical else "waiting_human",
    }
    store.append_jsonl("change_log.jsonl", rec)
    return rec


def log_run(store: Store, *, stage: str, variable: str, kind: str, git_commit: str, inputs: dict,
            outputs: dict, settings: dict, checks: dict, is_test: bool = False) -> dict:
    rec = {
        "id": next_id(store, "run_log.jsonl", "R"),
        "time": now_iso(),
        "stage": stage,
        "variable": variable,
        "kind": kind,
        "is_test_run": is_test,
        "git_commit": git_commit or "not stated",
        "input_fingerprints": inputs,
        "output_fingerprints": outputs,
        "settings": settings,
        "checks": checks,
    }
    store.append_jsonl("run_log.jsonl", rec)
    return rec


def log_dispute(store: Store, *, stage: str, variable: str, finding: dict, author_response: dict,
                route: str, outcome: str, judge_family: str | None, author_family: str | None,
                detail: dict) -> dict:
    rec = {
        "id": next_id(store, "dispute_log.jsonl", "X"),
        "date": now_iso(),
        "stage": stage,
        "variable": variable,
        "finding": finding,
        "author_response": author_response,
        "route": route,
        "outcome": outcome,
        "judge_family": judge_family,
        "author_family": author_family,
        "judge_sided_with_own_family": (
            (outcome == "author") == (judge_family == author_family)
            if route == "judge" and judge_family and author_family else None
        ),
        "detail": detail,
    }
    store.append_jsonl("dispute_log.jsonl", rec)
    return rec
