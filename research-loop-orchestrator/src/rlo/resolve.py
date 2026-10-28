"""Route the disputes that survive two review rounds.

1. Checkable error findings get no judge: the author writes a coded test and the result decides.
2. Judgment calls go to the human gate with both positions.
3. Anything left goes to a blinded judge; the verdict is logged with which family it sided with.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .models.base import Author, Finding, FindingResponse, Judge, JudgeVerdict, TestOutcome


@dataclass
class Resolution:
    finding: Finding
    author_response: FindingResponse
    route: str  # test | human | judge
    outcome: str  # author | reviewer | pending_human
    test: TestOutcome | None = None
    verdict: JudgeVerdict | None = None


@dataclass
class ResolveReport:
    resolutions: list[Resolution] = field(default_factory=list)

    def for_human(self) -> list[Resolution]:
        return [r for r in self.resolutions if r.route == "human"]

    def judge_family_rate(self, judge_family: str, author_family: str) -> float | None:
        judged = [r for r in self.resolutions if r.route == "judge" and r.verdict]
        if not judged:
            return None
        same = sum(1 for r in judged if (r.outcome == "author") == (judge_family == author_family))
        return same / len(judged)


def route_for(finding: Finding) -> str:
    if finding.kind == "error" and finding.checkable_by in ("test", "rule"):
        return "test"
    if finding.kind == "judgment":
        return "human"
    return "judge"


def resolve(
    disputes: list[tuple[Finding, FindingResponse]],
    author: Author,
    judge: Judge,
    context: dict,
    rng: random.Random | None = None,
) -> ResolveReport:
    rng = rng or random.Random()
    report = ResolveReport()
    for finding, response in disputes:
        route = route_for(finding)
        res = Resolution(finding=finding, author_response=response, route=route, outcome="pending_human")
        if route == "test":
            t = author.write_test(finding, context)
            res.test = t
            res.outcome = "author" if t.passed else "reviewer"
        elif route == "judge":
            author_pos = f"{response.reason}"
            reviewer_pos = f"{finding.claim}\nEvidence: {finding.evidence}\nProposed fix: {finding.proposed_fix}"
            # Blind: strip who said what, randomize order.
            a_is_author = rng.random() < 0.5
            pa, pb = (author_pos, reviewer_pos) if a_is_author else (reviewer_pos, author_pos)
            v = judge.judge(finding, pa, pb, context)
            winner_is_author = (v.winner == "A") == a_is_author
            v.sided_with = "author" if winner_is_author else "reviewer"
            res.verdict = v
            res.outcome = v.sided_with
        report.resolutions.append(res)
    return report
