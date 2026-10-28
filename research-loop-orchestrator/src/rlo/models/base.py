"""Model roles and the structured records they exchange.

The orchestrator never reads free text from a model to decide anything. Reviewers return
findings; authors return responses to findings; judges return a verdict. All are checked
against the schemas here before use.
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
    checkable_by: str = "none"  # test | rule | none: whether a coded check could settle it

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
    change: str = ""  # what was changed, if accepted
    reason: str = ""  # why rejected, if rejected

    def validate(self) -> None:
        if self.verdict not in ("accept", "reject"):
            raise ValueError(f"response {self.id}: bad verdict {self.verdict}")


@dataclass
class AuthorResult:
    summary: str
    files_written: list[str] = field(default_factory=list)
    responses: list[FindingResponse] = field(default_factory=list)
    stopped_on_budget: bool = False
    raw: dict = field(default_factory=dict)


@dataclass
class TestOutcome:
    finding_id: str
    test_path: str
    passed: bool  # True means the author's position held; False means the reviewer's did
    output: str


@dataclass
class JudgeVerdict:
    finding_id: str
    winner: str  # "A" or "B" as shown to the judge (blinded)
    reason: str
    # filled in by the orchestrator after unblinding:
    sided_with: str = ""  # "author" | "reviewer"


FINDINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "severity": {"type": "string", "enum": list(SEVERITIES)},
                    "kind": {"type": "string", "enum": list(KINDS)},
                    "claim": {"type": "string"},
                    "evidence": {"type": "string"},
                    "proposed_fix": {"type": "string"},
                    "checkable_by": {"type": "string", "enum": list(CHECKABLE)},
                },
                "required": ["id", "severity", "kind", "claim", "evidence", "proposed_fix", "checkable_by"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["findings"],
    "additionalProperties": False,
}

RESPONSES_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "responses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "verdict": {"type": "string", "enum": ["accept", "reject"]},
                    "change": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["id", "verdict", "change", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "responses"],
    "additionalProperties": False,
}

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "winner": {"type": "string", "enum": ["A", "B"]},
        "reason": {"type": "string"},
    },
    "required": ["winner", "reason"],
    "additionalProperties": False,
}

TEST_SCHEMA = {
    "type": "object",
    "properties": {
        "test_path": {"type": "string"},
        "author_position_held": {"type": "boolean"},
        "output": {"type": "string"},
    },
    "required": ["test_path", "author_position_held", "output"],
    "additionalProperties": False,
}


class Author(Protocol):
    """Does the work. Has tools. Returns a structured result."""

    def author(self, task: str, context: dict) -> AuthorResult: ...

    def respond(self, findings: list[Finding], context: dict) -> AuthorResult: ...

    def write_test(self, finding: Finding, context: dict) -> TestOutcome: ...


class Reviewer(Protocol):
    """Reads artifacts, no tools. Returns findings."""

    def review(self, artifacts: dict[str, str], context: dict) -> list[Finding]: ...

    def rereview(
        self, artifacts: dict[str, str], rejected: list[tuple[Finding, FindingResponse]], context: dict
    ) -> list[Finding]: ...


class Judge(Protocol):
    """Fresh session, blinded positions A and B."""

    def judge(self, finding: Finding, position_a: str, position_b: str, context: dict) -> JudgeVerdict: ...


def to_dict(obj) -> dict:
    return asdict(obj)
