"""Every model call is written to disk as a raw record before anything reads it.

Logs are built from these files by code, never from a model's own summary.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .state import now_iso


@dataclass
class CallRecord:
    call_id: str
    time: str
    role: str  # author | reviewer | judge | test
    provider: str  # anthropic | openai | fixture
    model: str
    stage: str
    variable: str
    round: int
    request: dict
    response: dict
    usage: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)


class CallLog:
    def __init__(self, calls_dir: Path):
        self.calls_dir = Path(calls_dir)
        self.calls_dir.mkdir(parents=True, exist_ok=True)
        self._seq = len(list(self.calls_dir.glob("*.json")))

    def record(self, **kwargs) -> CallRecord:
        rec = CallRecord(call_id=uuid.uuid4().hex[:12], time=now_iso(), **kwargs)
        self._seq += 1
        path = self.calls_dir / f"{rec.time.replace(':', '')}_{self._seq:05d}_{rec.role}_{rec.call_id}.json"
        path.write_text(json.dumps(asdict(rec), indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        return rec

    def all(self) -> list[CallRecord]:
        out = []
        for p in sorted(self.calls_dir.glob("*.json")):
            out.append(CallRecord(**json.loads(p.read_text(encoding="utf-8"))))
        return out
