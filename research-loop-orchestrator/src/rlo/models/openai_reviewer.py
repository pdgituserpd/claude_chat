"""The second model family as reviewer, via the OpenAI SDK. Reads artifacts, has no tools.

Not yet exercised against the live API: see README "Status".
"""

from __future__ import annotations

import json

from ..calls import CallLog
from .base import FINDINGS_SCHEMA, Finding


def _client():
    from openai import OpenAI  # lazy import

    return OpenAI()


def _bundle(artifacts: dict[str, str]) -> str:
    parts = []
    for name in sorted(artifacts):
        parts.append(f"===== FILE: {name} =====\n{artifacts[name]}\n")
    return "\n".join(parts)


class OpenAIReviewer:
    provider = "openai"

    def __init__(self, model: str, calls: CallLog, system_prompt: str):
        self.model = model
        self.calls = calls
        self.system = system_prompt
        self.client = _client()

    def _call(self, user_text: str, role_round: int, context: dict) -> list[Finding]:
        response = self.client.responses.create(
            model=self.model,
            instructions=self.system,
            input=user_text,
            text={"format": {"type": "json_schema", "name": "findings", "schema": FINDINGS_SCHEMA, "strict": True}},
        )
        raw = response.output_text
        self.calls.record(
            role="reviewer", provider=self.provider, model=self.model, stage=context["stage"],
            variable=context["variable"], round=role_round,
            request={"input": user_text[:5000] + ("..." if len(user_text) > 5000 else "")},
            response={"output_text": raw},
            usage=response.usage.model_dump() if getattr(response, "usage", None) else {},
        )
        data = json.loads(raw)
        return [Finding.from_dict(d) for d in data["findings"]]

    def review(self, artifacts: dict[str, str], context: dict) -> list[Finding]:
        user = (
            "Review the artifacts below against the task description. Report every deviation from the "
            "definition, every unstated choice, and every judgment call that should go to the human. "
            "Do not pad: an empty list is a valid answer.\n\nTASK\n" + context.get("task", "") +
            "\n\nARTIFACTS\n" + _bundle(artifacts)
        )
        return self._call(user, 1, context)

    def rereview(self, artifacts, rejected, context) -> list[Finding]:
        pairs = [{"finding": vars(f), "author_response": vars(r)} for f, r in rejected]
        user = (
            "The author rejected the findings below with reasons. Re-examine each against the current artifacts. "
            "Return only the findings you still stand behind, with the same ids and strengthened evidence; "
            "drop the ones the author's reason settles.\n\nREJECTED\n" + json.dumps(pairs, indent=2) +
            "\n\nARTIFACTS\n" + _bundle(artifacts)
        )
        return self._call(user, 2, context)
