"""Canned model behaviour for tests. No tokens spent.

A fixture file is JSON:
{
  "author": {"writes": {"spec/open_choices.json": "..."}, "summary": "..."},
  "responses": {"F1": {"verdict": "accept", "change": "..."}, "F2": {"verdict": "reject", "reason": "..."}},
  "fixes": {"F4": {"verdict": "accept", "change": "..."}},   # used when context["phase"] == "fix"
  "tests": {"F2": {"author_position_held": true, "output": "..."}},
  "reviews": [[{finding}, ...], [{finding}, ...]],
  "judge": {"F3": "A"}
}
"""

from __future__ import annotations

import json
from pathlib import Path

from ..calls import CallLog
from .base import AuthorResult, Finding, FindingResponse, JudgeVerdict, TestOutcome


class FixtureAuthor:
    provider = "fixture"

    def __init__(self, spec: dict, target: Path, calls: CallLog, model: str = "fixture-author"):
        self.spec = spec
        self.target = Path(target)
        self.calls = calls
        self.model = model

    def _rec(self, role: str, context: dict, request: dict, response: dict) -> None:
        self.calls.record(
            role=role, provider=self.provider, model=self.model, stage=context["stage"],
            variable=context["variable"], round=context.get("round", 0), request=request, response=response,
        )

    def author(self, task: str, context: dict) -> AuthorResult:
        a = self.spec.get("author", {})
        written = []
        for rel, content in a.get("writes", {}).items():
            p = self.target / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            written.append(rel)
        self._rec("author", context, {"task": task}, {"writes": written})
        return AuthorResult(summary=a.get("summary", "fixture author ran"), files_written=written)

    def respond(self, findings: list[Finding], context: dict) -> AuthorResult:
        table = self.spec.get("fixes", {}) if context.get("phase") == "fix" else self.spec.get("responses", {})
        out = []
        for f in findings:
            r = table.get(f.id, {"verdict": "accept", "change": "fixture accepted"})
            fr = FindingResponse(id=f.id, verdict=r["verdict"], change=r.get("change", ""), reason=r.get("reason", ""))
            fr.validate()
            out.append(fr)
            if fr.verdict == "accept":
                for rel, content in r.get("writes", {}).items():
                    p = self.target / rel
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(content, encoding="utf-8")
        self._rec("author", context, {"findings": [f.id for f in findings]}, {"responses": [vars(x) for x in out]})
        return AuthorResult(summary="fixture responded", responses=out)

    def write_test(self, finding: Finding, context: dict) -> TestOutcome:
        t = self.spec.get("tests", {}).get(finding.id, {"author_position_held": True, "output": "fixture test"})
        rel = f"tests/dispute_{finding.id}.txt"
        p = self.target / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(t["output"], encoding="utf-8")
        self._rec("test", context, {"finding": finding.id}, t)
        return TestOutcome(finding_id=finding.id, test_path=rel, passed=bool(t["author_position_held"]), output=t["output"])


class FixtureReviewer:
    provider = "fixture"

    def __init__(self, spec: dict, calls: CallLog, model: str = "fixture-reviewer"):
        self.spec = spec
        self.calls = calls
        self.model = model
        self._round = 0

    def _findings(self, idx: int) -> list[Finding]:
        reviews = self.spec.get("reviews", [])
        if idx >= len(reviews):
            return []
        return [Finding.from_dict(d) for d in reviews[idx]]

    def review(self, artifacts: dict[str, str], context: dict) -> list[Finding]:
        fs = self._findings(0)
        self.calls.record(
            role="reviewer", provider=self.provider, model=self.model, stage=context["stage"],
            variable=context["variable"], round=1, request={"artifacts": sorted(artifacts)},
            response={"findings": [vars(f) for f in fs]},
        )
        return fs

    def rereview(self, artifacts, rejected, context) -> list[Finding]:
        # Round two: the fixture may insist on some rejected findings, listed in reviews[1].
        fs = self._findings(1)
        self.calls.record(
            role="reviewer", provider=self.provider, model=self.model, stage=context["stage"],
            variable=context["variable"], round=2, request={"rejected": [f.id for f, _ in rejected]},
            response={"findings": [vars(f) for f in fs]},
        )
        return fs


class FixtureJudge:
    provider = "fixture"

    def __init__(self, spec: dict, calls: CallLog, model: str = "fixture-judge"):
        self.spec = spec
        self.calls = calls
        self.model = model

    def judge(self, finding: Finding, position_a: str, position_b: str, context: dict) -> JudgeVerdict:
        winner = self.spec.get("judge", {}).get(finding.id, "A")
        self.calls.record(
            role="judge", provider=self.provider, model=self.model, stage=context["stage"],
            variable=context["variable"], round=context.get("round", 0),
            request={"finding": finding.id, "A": position_a, "B": position_b},
            response={"winner": winner},
        )
        return JudgeVerdict(finding_id=finding.id, winner=winner, reason="fixture")


def load_fixture(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
