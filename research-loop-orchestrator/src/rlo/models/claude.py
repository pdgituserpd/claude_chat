"""Claude as author (with tools) and as blinded judge (no tools), via the Anthropic SDK.

Each role is a fresh conversation. Every request and response is written to the call log.
Not yet exercised against the live API: see README "Status".
"""

from __future__ import annotations

import json
from pathlib import Path

from ..calls import CallLog
from ..tools import TOOL_DEFINITIONS, Sandbox, ToolError
from .base import (
    RESPONSES_SCHEMA,
    TEST_SCHEMA,
    VERDICT_SCHEMA,
    AuthorResult,
    Finding,
    FindingResponse,
    JudgeVerdict,
    TestOutcome,
)

MAX_TOKENS = 16000


def _client():
    import anthropic  # imported lazily so tests never need the package

    return anthropic.Anthropic()


def _text(message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


class ClaudeAuthor:
    provider = "anthropic"

    def __init__(self, model: str, target: Path, readable: list[str], calls: CallLog,
                 system_prompt: str, max_model_calls: int, max_tool_calls: int):
        self.model = model
        self.sandbox = Sandbox(target, readable)
        self.calls = calls
        self.system = system_prompt
        self.max_model_calls = max_model_calls
        self.max_tool_calls = max_tool_calls
        self.model_calls = 0
        self.client = _client()

    # -- the loop ---------------------------------------------------------
    def _run(self, role: str, user_text: str, context: dict, output_schema: dict | None) -> tuple[str, bool]:
        """Manual agentic loop with tools. Returns (final text, stopped_on_budget)."""
        messages = [{"role": "user", "content": user_text}]
        kwargs = dict(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=[{"type": "text", "text": self.system, "cache_control": {"type": "ephemeral"}}],
            tools=TOOL_DEFINITIONS,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
        )
        final = ""
        while True:
            if self.model_calls >= self.max_model_calls or self.sandbox.tool_calls >= self.max_tool_calls:
                return final, True
            response = self.client.messages.create(messages=messages, **kwargs)
            self.model_calls += 1
            self.calls.record(
                role=role, provider=self.provider, model=self.model, stage=context["stage"],
                variable=context["variable"], round=context.get("round", 0),
                request={"messages": messages, "system": self.system[:200] + "..."},
                response=response.to_dict(),
                usage=response.usage.to_dict() if response.usage else {},
            )
            if response.stop_reason == "refusal":
                raise RuntimeError(f"author refused: {response.stop_details}")
            messages.append({"role": "assistant", "content": response.content})
            if response.stop_reason == "max_tokens":
                messages.append({"role": "user", "content": "You hit the output limit. Continue, more briefly."})
                continue
            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                final = _text(response)
                if output_schema is not None:
                    # Ask for the structured record as the last call, with no tools.
                    return self._structured(messages, output_schema, role, context), False
                return final, False
            results = []
            for tu in tool_uses:
                try:
                    out = self.sandbox.dispatch(tu.name, dict(tu.input))
                    results.append({"type": "tool_result", "tool_use_id": tu.id, "content": out})
                except ToolError as e:
                    results.append({"type": "tool_result", "tool_use_id": tu.id, "content": str(e), "is_error": True})
            messages.append({"role": "user", "content": results})

    def _structured(self, messages: list, schema: dict, role: str, context: dict) -> str:
        messages = messages + [{"role": "user", "content": "Now return the structured record described in your instructions."}]
        response = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=self.system,
            messages=messages,
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": schema}},
        )
        self.model_calls += 1
        self.calls.record(
            role=role, provider=self.provider, model=self.model, stage=context["stage"],
            variable=context["variable"], round=context.get("round", 0),
            request={"structured": True}, response=response.to_dict(),
            usage=response.usage.to_dict() if response.usage else {},
        )
        return _text(response)

    # -- roles -------------------------------------------------------------
    def author(self, task: str, context: dict) -> AuthorResult:
        text, stopped = self._run("author", task, context, None)
        return AuthorResult(summary=text, stopped_on_budget=stopped)

    def respond(self, findings: list[Finding], context: dict) -> AuthorResult:
        prompt = (
            "A reviewer from a different model family returned the findings below on your work. "
            "For each one, either accept it and make the change in the repository, or reject it with a reason "
            "that points at the definition, the data or the literature. Do not accept to be agreeable; do not "
            "reject to save work.\n\n" + json.dumps([vars(f) for f in findings], indent=2)
        )
        text, stopped = self._run("author", prompt, context, RESPONSES_SCHEMA)
        if stopped:
            return AuthorResult(summary="stopped on budget", stopped_on_budget=True)
        data = json.loads(text)
        responses = []
        for r in data["responses"]:
            fr = FindingResponse(**r)
            fr.validate()
            responses.append(fr)
        return AuthorResult(summary=data["summary"], responses=responses, raw=data)

    def write_test(self, finding: Finding, context: dict) -> TestOutcome:
        prompt = (
            "You and a reviewer disagree on the finding below, and it is the kind of question a coded check can settle. "
            "Write a small, self-contained test or fake case in the repository that would decide it, run it, and "
            "report honestly whether your position held. The test must be able to fail.\n\n"
            + json.dumps(vars(finding), indent=2)
        )
        text, stopped = self._run("test", prompt, context, TEST_SCHEMA)
        if stopped:
            return TestOutcome(finding_id=finding.id, test_path="", passed=False, output="stopped on budget")
        data = json.loads(text)
        return TestOutcome(finding_id=finding.id, test_path=data["test_path"],
                           passed=bool(data["author_position_held"]), output=data["output"])


class ClaudeJudge:
    provider = "anthropic"

    def __init__(self, model: str, calls: CallLog, system_prompt: str):
        self.model = model
        self.calls = calls
        self.system = system_prompt
        self.client = _client()

    def judge(self, finding: Finding, position_a: str, position_b: str, context: dict) -> JudgeVerdict:
        user = (
            "Two parties disagree about the finding below. Decide which position is better supported by the "
            "definition, the data and the literature. You are not told who wrote which.\n\n"
            f"FINDING\n{json.dumps(vars(finding), indent=2)}\n\nPOSITION A\n{position_a}\n\nPOSITION B\n{position_b}"
        )
        response = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=self.system,
            messages=[{"role": "user", "content": user}],
            thinking={"type": "adaptive"},
            output_config={"effort": "high", "format": {"type": "json_schema", "schema": VERDICT_SCHEMA}},
        )
        self.calls.record(
            role="judge", provider=self.provider, model=self.model, stage=context["stage"],
            variable=context["variable"], round=context.get("round", 0),
            request={"finding": finding.id, "A": position_a, "B": position_b},
            response=response.to_dict(), usage=response.usage.to_dict() if response.usage else {},
        )
        data = json.loads(_text(response))
        return JudgeVerdict(finding_id=finding.id, winner=data["winner"], reason=data["reason"])
