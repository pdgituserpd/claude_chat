"""Claude through the Anthropic SDK (API keys): tool-using roles and the blinded judge.

Each role call is a fresh conversation. Every request and response is written to the call
log. Not yet exercised against the live API: see README "Status".
"""

from __future__ import annotations

import json
from pathlib import Path

from ..calls import CallLog
from ..tools import TOOL_DEFINITIONS, Sandbox, ToolError
from .base import (RESPONSES_SCHEMA, SUMMARY_SCHEMA, TEST_PLAN_SCHEMA, VERDICT_SCHEMA, Finding, FindingResponse,
                   JudgeVerdict, TaskResult, TestPlan, extract_json)
from .prompts import judge_prompt, plan_test_prompt, respond_prompt

MAX_TOKENS = 16000


def _client():
    import anthropic  # lazy so tests never need the package

    return anthropic.Anthropic()


def _text(message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


class ClaudeAPIAgent:
    provider = "anthropic"
    family = "anthropic"

    def __init__(self, model: str, calls: CallLog, system_prompt: str, role: str,
                 max_model_calls: int, max_tool_calls: int, readable: list[str] | None = None):
        self.model = model
        self.calls = calls
        self.system = system_prompt
        self.role = role
        self.max_model_calls = max_model_calls
        self.max_tool_calls = max_tool_calls
        self.readable = readable or []
        self.model_calls = 0
        self.client = _client()

    def _run(self, role: str, user_text: str, workdir: Path, context: dict, schema: dict) -> tuple[dict | None, bool]:
        sandbox = Sandbox(workdir, self.readable)
        messages = [{"role": "user", "content": user_text}]
        kwargs = dict(model=self.model, max_tokens=MAX_TOKENS,
                      system=[{"type": "text", "text": self.system, "cache_control": {"type": "ephemeral"}}],
                      tools=TOOL_DEFINITIONS, thinking={"type": "adaptive"}, output_config={"effort": "high"})
        while True:
            if self.model_calls >= self.max_model_calls or sandbox.tool_calls >= self.max_tool_calls:
                return None, True
            response = self.client.messages.create(messages=messages, **kwargs)
            self.model_calls += 1
            self.calls.record(role=role, provider=self.provider, model=self.model, stage=context["stage"],
                              variable=context["variable"], round=context.get("round", 0),
                              request={"messages": messages}, response=response.to_dict(),
                              usage=response.usage.to_dict() if response.usage else {})
            if response.stop_reason == "refusal":
                raise RuntimeError(f"{role} refused: {response.stop_details}")
            messages.append({"role": "assistant", "content": response.content})
            if response.stop_reason == "max_tokens":
                messages.append({"role": "user", "content": "You hit the output limit. Continue, more briefly."})
                continue
            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                return self._structured(messages, schema, role, context), False
            results = []
            for tu in tool_uses:
                try:
                    out = sandbox.dispatch(tu.name, dict(tu.input))
                    results.append({"type": "tool_result", "tool_use_id": tu.id, "content": out})
                except ToolError as e:
                    results.append({"type": "tool_result", "tool_use_id": tu.id, "content": str(e), "is_error": True})
            messages.append({"role": "user", "content": results})

    def _structured(self, messages: list, schema: dict, role: str, context: dict) -> dict:
        messages = messages + [{"role": "user", "content": "Now return the structured record described in your instructions."}]
        response = self.client.messages.create(
            model=self.model, max_tokens=MAX_TOKENS, system=self.system, messages=messages,
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": schema}})
        self.model_calls += 1
        self.calls.record(role=role, provider=self.provider, model=self.model, stage=context["stage"],
                          variable=context["variable"], round=context.get("round", 0),
                          request={"structured": True}, response=response.to_dict(),
                          usage=response.usage.to_dict() if response.usage else {})
        return json.loads(extract_json(_text(response)))

    def run_task(self, task: str, workdir, context: dict) -> TaskResult:
        data, stopped = self._run(self.role, task, Path(workdir), context, SUMMARY_SCHEMA)
        if stopped:
            return TaskResult(summary="stopped on budget", stopped_on_budget=True)
        return TaskResult(summary=data["summary"], files_written=data["files_written"], raw=data)

    def respond(self, findings: list[Finding], workdir, context: dict) -> TaskResult:
        data, stopped = self._run(self.role, respond_prompt(findings), Path(workdir), context, RESPONSES_SCHEMA)
        if stopped:
            return TaskResult(summary="stopped on budget", stopped_on_budget=True)
        responses = []
        for r in data["responses"]:
            fr = FindingResponse(**r)
            fr.validate()
            responses.append(fr)
        return TaskResult(summary=data["summary"], responses=responses, raw=data)

    def plan_test(self, finding: Finding, workdir, context: dict) -> TestPlan | None:
        data, stopped = self._run("test", plan_test_prompt(finding), Path(workdir), context, TEST_PLAN_SCHEMA)
        if stopped or data is None:
            return None
        return TestPlan(finding_id=finding.id, **data)


class ClaudeAPIJudge:
    provider = "anthropic"
    family = "anthropic"

    def __init__(self, model: str, calls: CallLog, system_prompt: str):
        self.model = model
        self.calls = calls
        self.system = system_prompt
        self.client = _client()

    def judge(self, finding: Finding, position_a: str, position_b: str, context: dict) -> JudgeVerdict:
        user = judge_prompt(finding, position_a, position_b)
        response = self.client.messages.create(
            model=self.model, max_tokens=MAX_TOKENS, system=self.system, messages=[{"role": "user", "content": user}],
            thinking={"type": "adaptive"},
            output_config={"effort": "high", "format": {"type": "json_schema", "schema": VERDICT_SCHEMA}})
        self.calls.record(role="judge", provider=self.provider, model=self.model, stage=context["stage"],
                          variable=context["variable"], round=context.get("round", 0),
                          request={"finding": finding.id, "A": position_a, "B": position_b},
                          response=response.to_dict(), usage=response.usage.to_dict() if response.usage else {})
        data = json.loads(extract_json(_text(response)))
        return JudgeVerdict(finding_id=finding.id, winner=data["winner"], reason=data["reason"])
