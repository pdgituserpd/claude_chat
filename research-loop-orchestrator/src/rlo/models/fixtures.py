"""Canned model behaviour for tests. No tokens spent, no programs called.

Fixture JSON, every key optional:
{
  "tasks":     {"<step>": {"summary": "...", "writes": {"path": "content"}}},
  "reviews":   {"<step>": [[finding, ...], [finding, ...]]},        # round 1, round 2
  "responses": {"F1": {"verdict": "accept", "change": "...", "writes": {...}}, "F2": {"verdict": "reject", "reason": "..."}},
  "fixes":     {"F4": {"verdict": "accept", "change": "..."}},     # after a dispute is settled against the author
  "tests":     {"F2": {"files": {"path": "content"}, "test_command": ["python", "tests/x.py"], "subject": "R/x.R", "mutant": "tests/x_mutant.R"}},
  "mutant_confirm": {"F2": true},
  "judge":     {"F4": "A"},
  "check_fixes": {"<step>": {"writes": {...}}}                       # what the author does when a check fails
}
Review findings are keyed by step; responses, tests and judge by finding id.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..calls import CallLog
from .base import Finding, FindingResponse, JudgeVerdict, TaskResult, TestPlan


def _write_all(workdir: Path, writes: dict) -> list[str]:
    out = []
    for rel, content in writes.items():
        p = Path(workdir) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        out.append(rel)
    return out


class FixtureToolAgent:
    provider = "fixture"
    family = "fixture"

    def __init__(self, spec: dict, calls: CallLog, role: str = "author", model: str = "fixture"):
        self.spec = spec
        self.calls = calls
        self.role = role
        self.model = model

    def _rec(self, context: dict, request: dict, response: dict, role: str | None = None) -> None:
        self.calls.record(role=role or self.role, provider=self.provider, model=self.model, stage=context["stage"],
                          variable=context["variable"], round=context.get("round", 0), request=request, response=response)

    def run_task(self, task: str, workdir, context: dict) -> TaskResult:
        key = context.get("check_fix_for") or context.get("step", "")
        if context.get("bug"):
            key = f"{key}:{context['bug']}"
        table = self.spec.get("check_fixes", {}) if context.get("check_fix_for") else self.spec.get("tasks", {})
        t = table.get(key, {})
        written = _write_all(workdir, t.get("writes", {}))
        self._rec(context, {"task": task[:300], "step": key}, {"writes": written})
        return TaskResult(summary=t.get("summary", f"fixture {self.role} ran {key}"), files_written=written)

    def respond(self, findings: list[Finding], workdir, context: dict) -> TaskResult:
        table = self.spec.get("fixes", {}) if context.get("phase") == "fix" else self.spec.get("responses", {})
        out = []
        for f in findings:
            r = table.get(f.id, {"verdict": "accept", "change": "fixture accepted"})
            fr = FindingResponse(id=f.id, verdict=r["verdict"], change=r.get("change", ""), reason=r.get("reason", ""))
            fr.validate()
            out.append(fr)
            if fr.verdict == "accept":
                _write_all(workdir, r.get("writes", {}))
        self._rec(context, {"findings": [f.id for f in findings]}, {"responses": [vars(x) for x in out]})
        return TaskResult(summary="fixture responded", responses=out)

    def plan_test(self, finding: Finding, workdir, context: dict) -> TestPlan | None:
        t = self.spec.get("tests", {}).get(finding.id)
        self._rec(context, {"finding": finding.id}, {"plan": t}, role="test")
        if not t:
            return None
        _write_all(workdir, t.get("files", {}))
        return TestPlan(finding_id=finding.id, test_command=t["test_command"], subject=t["subject"],
                        mutant=t["mutant"], note=t.get("note", ""))


class FixtureReviewer:
    provider = "fixture"
    family = "fixture"

    def __init__(self, spec: dict, calls: CallLog, model: str = "fixture-reviewer"):
        self.spec = spec
        self.calls = calls
        self.model = model

    def _findings(self, step: str, idx: int) -> list[Finding]:
        reviews = self.spec.get("reviews", {}).get(step, [])
        if idx >= len(reviews):
            return []
        return [Finding.from_dict(d) for d in reviews[idx]]

    def _rec(self, context, rnd, request, response):
        self.calls.record(role="reviewer", provider=self.provider, model=self.model, stage=context["stage"],
                          variable=context["variable"], round=rnd, request=request, response=response)

    def review(self, artifacts, context) -> list[Finding]:
        fs = self._findings(context.get("step", ""), 0)
        self._rec(context, 1, {"artifacts": sorted(artifacts)}, {"findings": [vars(f) for f in fs]})
        return fs

    def rereview(self, artifacts, rejected, context) -> list[Finding]:
        fs = self._findings(context.get("step", ""), 1)
        self._rec(context, 2, {"rejected": [f.id for f, _ in rejected]}, {"findings": [vars(f) for f in fs]})
        return fs

    def confirm_mutant(self, finding, diff, context) -> tuple[bool, str]:
        ok = bool(self.spec.get("mutant_confirm", {}).get(finding.id, True))
        self._rec(context, context.get("round", 0), {"confirm": finding.id, "diff": diff[:500]}, {"matches_claim": ok})
        return ok, "fixture"


class FixtureJudge:
    provider = "fixture"
    family = "fixture"

    def __init__(self, spec: dict, calls: CallLog, model: str = "fixture-judge"):
        self.spec = spec
        self.calls = calls
        self.model = model

    def judge(self, finding, position_a, position_b, context) -> JudgeVerdict:
        winner = self.spec.get("judge", {}).get(finding.id, "A")
        self.calls.record(role="judge", provider=self.provider, model=self.model, stage=context["stage"],
                          variable=context["variable"], round=context.get("round", 0),
                          request={"finding": finding.id, "A": position_a, "B": position_b}, response={"winner": winner})
        return JudgeVerdict(finding_id=finding.id, winner=winner, reason="fixture")


def load_fixture(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
