"""The second model family as reviewer through the OpenAI SDK (API keys). Reads artifacts, no tools.

Not yet exercised against the live API: see README "Status".
"""

from __future__ import annotations

import json

from ..calls import CallLog
from .base import CONFIRM_SCHEMA, FINDINGS_SCHEMA, Finding, extract_json
from .prompts import bundle_artifacts, confirm_prompt, rereview_prompt, review_prompt


def _client():
    from openai import OpenAI  # lazy import

    return OpenAI()


class OpenAIReviewer:
    provider = "openai"
    family = "openai"

    def __init__(self, model: str, calls: CallLog, system_prompt: str):
        self.model = model
        self.calls = calls
        self.system = system_prompt
        self.client = _client()

    def _call(self, user_text: str, schema: dict, name: str, rnd: int, context: dict) -> dict:
        response = self.client.responses.create(
            model=self.model, instructions=self.system, input=user_text,
            text={"format": {"type": "json_schema", "name": name, "schema": schema, "strict": True}})
        raw = response.output_text
        self.calls.record(role="reviewer", provider=self.provider, model=self.model, stage=context["stage"],
                          variable=context["variable"], round=rnd,
                          request={"input": user_text[:5000] + ("..." if len(user_text) > 5000 else "")},
                          response={"output_text": raw},
                          usage=response.usage.model_dump() if getattr(response, "usage", None) else {})
        return json.loads(extract_json(raw))

    def review(self, artifacts, context) -> list[Finding]:
        data = self._call(review_prompt(context.get("task", ""), bundle_artifacts(artifacts)), FINDINGS_SCHEMA, "findings", 1, context)
        return [Finding.from_dict(d) for d in data["findings"]]

    def rereview(self, artifacts, rejected, context) -> list[Finding]:
        data = self._call(rereview_prompt(rejected, bundle_artifacts(artifacts)), FINDINGS_SCHEMA, "findings", 2, context)
        return [Finding.from_dict(d) for d in data["findings"]]

    def confirm_mutant(self, finding, diff, context) -> tuple[bool, str]:
        data = self._call(confirm_prompt(finding, diff), CONFIRM_SCHEMA, "confirm", context.get("round", 0), context)
        return bool(data["matches_claim"]), data["reason"]
