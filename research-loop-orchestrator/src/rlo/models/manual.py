"""Manual mode: you are the transport. The program writes a bundle, stops, and resumes once the
answer file exists.

Each pending request has a deterministic key, so re-running `rlo run` after the answer is
saved finds it. The answer is a JSON file matching the schema named in the bundle.
`rlo ingest` validates and places an answer file for you.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..calls import CallLog
from .base import (CONFIRM_SCHEMA, FINDINGS_SCHEMA, RESPONSES_SCHEMA, SUMMARY_SCHEMA, TEST_PLAN_SCHEMA,
                   VERDICT_SCHEMA, Finding, FindingResponse, JudgeVerdict, TaskResult, TestPlan)
from .prompts import (bundle_artifacts, confirm_prompt, judge_prompt, plan_test_prompt, record_instruction,
                      rereview_prompt, respond_prompt, review_prompt)


class NeedsHuman(Exception):
    def __init__(self, bundle: Path, answer: Path, schema_name: str):
        super().__init__(f"waiting for {answer}")
        self.bundle = bundle
        self.answer = answer
        self.schema_name = schema_name


SCHEMAS = {"summary": SUMMARY_SCHEMA, "responses": RESPONSES_SCHEMA, "findings": FINDINGS_SCHEMA,
           "test_plan": TEST_PLAN_SCHEMA, "confirm": CONFIRM_SCHEMA, "verdict": VERDICT_SCHEMA}


class ManualBase:
    provider = "manual"
    family = "human-relayed"

    def __init__(self, calls: CallLog, manual_dir: Path, system_prompt: str, role: str, model: str = "manual"):
        self.calls = calls
        self.manual_dir = Path(manual_dir)
        self.system = system_prompt
        self.role = role
        self.model = model

    def _key(self, context: dict, purpose: str) -> str:
        return f"{context['stage']}_{context['variable']}_{context.get('step','')}_{self.role}_{purpose}_r{context.get('round', 0)}"

    def _exchange(self, context: dict, purpose: str, prompt: str, schema_name: str, workdir: Path | None) -> dict:
        key = self._key(context, purpose)
        bundle = self.manual_dir / f"{key}.md"
        answer = self.manual_dir / f"{key}.answer.json"
        if answer.exists():
            data = json.loads(answer.read_text(encoding="utf-8"))
            self.calls.record(role=self.role, provider=self.provider, model=self.model, stage=context["stage"],
                              variable=context["variable"], round=context.get("round", 0),
                              request={"bundle": str(bundle)}, response=data, meta={"answer_file": str(answer)})
            return data
        where = f"Work in the folder: {workdir}\n\n" if workdir else ""
        text = (f"# Manual request: {self.role} / {purpose}\n\n"
                f"Paste everything below the line into the {self.role} chat window. "
                f"Save the reply as JSON at:\n\n    {answer}\n\nthen run `rlo run` again "
                f"(or `rlo ingest --file <reply.json>` to validate and place it).\n\n{where}---\n\n"
                + self.system + "\n\n" + prompt + record_instruction(SCHEMAS[schema_name], None))
        bundle.write_text(text, encoding="utf-8")
        raise NeedsHuman(bundle, answer, schema_name)


class ManualToolAgent(ManualBase):
    def run_task(self, task, workdir, context) -> TaskResult:
        data = self._exchange(context, "task", task, "summary", Path(workdir))
        return TaskResult(summary=data["summary"], files_written=list(data.get("files_written", [])), raw=data)

    def respond(self, findings, workdir, context) -> TaskResult:
        purpose = "fix" if context.get("phase") == "fix" else "respond"
        data = self._exchange(context, purpose, respond_prompt(findings), "responses", Path(workdir))
        responses = []
        for r in data["responses"]:
            fr = FindingResponse(**r)
            fr.validate()
            responses.append(fr)
        return TaskResult(summary=data["summary"], responses=responses, raw=data)

    def plan_test(self, finding, workdir, context) -> TestPlan | None:
        data = self._exchange(context, f"test_{finding.id}", plan_test_prompt(finding), "test_plan", Path(workdir))
        return TestPlan(finding_id=finding.id, **data)


class ManualReviewer(ManualBase):
    def review(self, artifacts, context) -> list[Finding]:
        data = self._exchange(context, "review", review_prompt(context.get("task", ""), bundle_artifacts(artifacts)), "findings", None)
        return [Finding.from_dict(d) for d in data["findings"]]

    def rereview(self, artifacts, rejected, context) -> list[Finding]:
        data = self._exchange(context, "rereview", rereview_prompt(rejected, bundle_artifacts(artifacts)), "findings", None)
        return [Finding.from_dict(d) for d in data["findings"]]

    def confirm_mutant(self, finding, diff, context) -> tuple[bool, str]:
        data = self._exchange(context, f"confirm_{finding.id}", confirm_prompt(finding, diff), "confirm", None)
        return bool(data["matches_claim"]), data["reason"]


class ManualJudge(ManualBase):
    def judge(self, finding, position_a, position_b, context) -> JudgeVerdict:
        data = self._exchange(context, f"judge_{finding.id}", judge_prompt(finding, position_a, position_b), "verdict", None)
        return JudgeVerdict(finding_id=finding.id, winner=data["winner"], reason=data["reason"])
