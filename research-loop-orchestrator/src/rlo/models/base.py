"""Model roles and the structured records they exchange.

The orchestrator never decides anything from free text. Reviewers return findings; tool
roles return responses to findings or a test plan; judges return a verdict. Every record is
checked against the schemas here before use.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Protocol

SEVERITIES = ("high", "medium", "low")
KINDS = ("error", "judgment")
CHECKABLE = ("test", "rule", "none")


@dataclass
class Finding:
    id: str
    severity: str
    kind: str  # error: has a right answer to check against. judgment: no right answer.
    claim: str
    evidence: str
    proposed_fix: str
    checkable_by: str = "none"

    def validate(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"finding {self.id}: bad severity {self.severity}")
        if self.kind not in KINDS:
            raise ValueError(f"finding {self.id}: bad kind {self.kind}")
        if self.checkable_by not in CHECKABLE:
            raise ValueError(f"finding {self.id}: bad checkable_by {self.checkable_by}")

    @classmethod
    def from_dict(cls, d: dict) -> "Finding":
        f = cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})
        f.validate()
        return f


@dataclass
class FindingResponse:
    id: str
    verdict: str  # accept | reject
    change: str = ""
    reason: str = ""

    def validate(self) -> None:
        if self.verdict not in ("accept", "reject"):
            raise ValueError(f"response {self.id}: bad verdict {self.verdict}")


@dataclass
class TaskResult:
    summary: str
    files_written: list[str] = field(default_factory=list)
    responses: list[FindingResponse] = field(default_factory=list)
    stopped_on_budget: bool = False
    raw: dict = field(default_factory=dict)


@dataclass
class TestPlan:
    """What a tool role hands back when asked to settle a dispute with a coded test.

    The orchestrator runs `test_command` twice, with RLO_SUBJECT set to `mutant` (must fail)
    and then to `subject` (decides). The reviewer confirms the mutant carries the claimed error.
    """
    finding_id: str
    test_command: list[str]
    subject: str  # path, relative to the work folder, of the real file under test
    mutant: str   # path of a copy carrying the claimed error
    note: str = ""


@dataclass
class TestOutcome:
    finding_id: str
    plan: TestPlan | None
    mutant_failed: bool | None      # the test must fail on the mutant to count
    subject_passed: bool | None     # True: the author's position held
    reviewer_confirmed: bool | None # the reviewer agreed the mutant matches its claim
    valid: bool                     # mutant_failed and reviewer_confirmed
    output: str


@dataclass
class JudgeVerdict:
    finding_id: str
    winner: str  # "A" or "B" as shown to the judge (blinded)
    reason: str
    sided_with: str = ""  # filled after unblinding: author | reviewer


FINDINGS_SCHEMA = {
    "type": "object",
    "properties": {"findings": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"}, "severity": {"type": "string", "enum": list(SEVERITIES)},
            "kind": {"type": "string", "enum": list(KINDS)}, "claim": {"type": "string"},
            "evidence": {"type": "string"}, "proposed_fix": {"type": "string"},
            "checkable_by": {"type": "string", "enum": list(CHECKABLE)},
        },
        "required": ["id", "severity", "kind", "claim", "evidence", "proposed_fix", "checkable_by"],
        "additionalProperties": False}}},
    "required": ["findings"], "additionalProperties": False,
}

RESPONSES_SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"}, "responses": {"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "verdict": {"type": "string", "enum": ["accept", "reject"]},
                       "change": {"type": "string"}, "reason": {"type": "string"}},
        "required": ["id", "verdict", "change", "reason"], "additionalProperties": False}}},
    "required": ["summary", "responses"], "additionalProperties": False,
}

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {"winner": {"type": "string", "enum": ["A", "B"]}, "reason": {"type": "string"}},
    "required": ["winner", "reason"], "additionalProperties": False,
}

TEST_PLAN_SCHEMA = {
    "type": "object",
    "properties": {"test_command": {"type": "array", "items": {"type": "string"}}, "subject": {"type": "string"},
                   "mutant": {"type": "string"}, "note": {"type": "string"}},
    "required": ["test_command", "subject", "mutant", "note"], "additionalProperties": False,
}

CONFIRM_SCHEMA = {
    "type": "object",
    "properties": {"matches_claim": {"type": "boolean"}, "reason": {"type": "string"}},
    "required": ["matches_claim", "reason"], "additionalProperties": False,
}

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"}, "files_written": {"type": "array", "items": {"type": "string"}}},
    "required": ["summary", "files_written"], "additionalProperties": False,
}


class ToolAgent(Protocol):
    """A role with tools (author, builder, planter). Works inside one folder."""

    def run_task(self, task: str, workdir, context: dict) -> TaskResult: ...

    def respond(self, findings: list[Finding], workdir, context: dict) -> TaskResult: ...

    def plan_test(self, finding: Finding, workdir, context: dict) -> TestPlan | None: ...


class Reviewer(Protocol):
    """Reads artifacts, has no tools."""

    def review(self, artifacts: dict[str, str], context: dict) -> list[Finding]: ...

    def rereview(self, artifacts: dict[str, str], rejected: list[tuple[Finding, FindingResponse]], context: dict) -> list[Finding]: ...

    def confirm_mutant(self, finding: Finding, diff: str, context: dict) -> tuple[bool, str]: ...


class Judge(Protocol):
    def judge(self, finding: Finding, position_a: str, position_b: str, context: dict) -> JudgeVerdict: ...


def to_dict(obj) -> dict:
    return asdict(obj)


def extract_json(text: str) -> str:
    """Pull a JSON object out of a model reply that may wrap it in prose or a code fence."""
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in reply")
    return s[start:end + 1]
