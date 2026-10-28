"""Stage configuration, loaded from TOML files in the orchestrator's stages/ folder."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[2]
STAGES_DIR = PKG_ROOT / "stages"
PROMPTS_DIR = PKG_ROOT / "prompts"


@dataclass
class Budget:
    max_model_calls: int = 40
    max_tool_calls: int = 200


@dataclass
class StageConfig:
    name: str
    title: str
    inputs: list[str]  # globs relative to the target repo the author may read
    outputs: list[str]  # globs relative to the target repo that count as the stage's product
    author_prompt: str  # file name under prompts/
    reviewer_prompt: str
    judge_prompt: str
    gate: str  # "human" or "auto"
    gate_items_file: str | None  # JSON produced by the author listing open choices
    review_rounds: int = 2
    budget: Budget = field(default_factory=Budget)
    author_model: str = "claude-opus-5-5"
    reviewer_model: str = "gpt-5"
    judge_model: str = "claude-opus-5-5"

    def prompt_text(self, which: str) -> str:
        name = getattr(self, f"{which}_prompt")
        return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def load_stage(name: str, stages_dir: Path = STAGES_DIR) -> StageConfig:
    path = stages_dir / f"{name}.toml"
    if not path.exists():
        raise FileNotFoundError(f"no stage config at {path}")
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    budget = Budget(**raw.pop("budget", {}))
    models = raw.pop("models", {})
    return StageConfig(
        name=name,
        budget=budget,
        author_model=models.get("author", "claude-opus-5-5"),
        reviewer_model=models.get("reviewer", "gpt-5"),
        judge_model=models.get("judge", "claude-opus-5-5"),
        **raw,
    )
