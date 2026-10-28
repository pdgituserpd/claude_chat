"""Pipeline state lives in the target repo under .rlo/ so git is the database."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class StageState:
    stage: str
    variable: str
    status: str = "not_started"  # not_started | authoring | reviewing | resolving | waiting_human | done | stopped
    round: int = 0
    started_at: str = ""
    updated_at: str = ""
    gate_file: str | None = None
    notes: list[str] = field(default_factory=list)
    model_calls: int = 0
    tool_calls: int = 0

    def touch(self, status: str | None = None) -> None:
        if status:
            self.status = status
        self.updated_at = now_iso()


class Store:
    """Reads and writes .rlo/ inside a target repository."""

    def __init__(self, target: Path):
        self.target = Path(target).resolve()
        self.root = self.target / ".rlo"
        self.calls_dir = self.root / "calls"
        self.rounds_dir = self.root / "rounds"
        self.snapshots_dir = self.root / "snapshots"
        for d in (self.root, self.calls_dir, self.rounds_dir, self.snapshots_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.gates_dir = self.target / "gates"
        self.logs_dir = self.target / "logs"
        self.gates_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

    def _state_path(self, stage: str, variable: str) -> Path:
        return self.root / f"state_{stage}_{variable}.json"

    def load(self, stage: str, variable: str) -> StageState:
        p = self._state_path(stage, variable)
        if p.exists():
            return StageState(**json.loads(p.read_text(encoding="utf-8")))
        st = StageState(stage=stage, variable=variable, started_at=now_iso())
        st.touch()
        return st

    def save(self, st: StageState) -> None:
        st.touch()
        self._state_path(st.stage, st.variable).write_text(
            json.dumps(asdict(st), indent=2), encoding="utf-8"
        )

    def all_states(self) -> list[StageState]:
        out = []
        for p in sorted(self.root.glob("state_*.json")):
            out.append(StageState(**json.loads(p.read_text(encoding="utf-8"))))
        return out

    def write_round(self, st: StageState, name: str, payload: object) -> Path:
        p = self.rounds_dir / f"{st.stage}_{st.variable}_{name}.json"
        p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return p

    def append_jsonl(self, filename: str, record: dict) -> None:
        p = self.logs_dir / filename
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def read_jsonl(self, filename: str) -> list[dict]:
        p = self.logs_dir / filename
        if not p.exists():
            return []
        return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
