"""Stage configuration: a stage is an ordered list of steps, loaded from stages/<name>.toml.

Step kinds
  task          a tool-using role (author, builder, planter) does a job; optional review loop
  check         a command in the target repo must exit 0; the author may fix and rerun
  compare       two CSV outputs are compared row by row on key columns
  planted_bugs  realistic bugs are planted and every listed layer is run on each one
  human         the program writes a checklist and stops
  snapshot      outputs (and the definition) are fingerprinted; sign-off rule applies
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[2]
STAGES_DIR = PKG_ROOT / "stages"
PROMPTS_DIR = PKG_ROOT / "prompts"

STEP_KINDS = ("task", "check", "compare", "planted_bugs", "human", "snapshot")
TOOL_ROLES = ("author", "builder", "planter")


@dataclass
class Budget:
    max_model_calls: int = 40
    max_tool_calls: int = 200


@dataclass
class Step:
    name: str
    kind: str
    title: str = ""
    # task
    role: str = "author"
    prompt: str = ""
    inputs: list[str] = field(default_factory=list)   # globs the role may read; empty = whole repo
    outputs: list[str] = field(default_factory=list)  # globs that are this step's product
    isolated: bool = False                            # run in a blinded folder holding only `inputs`
    review: bool = False                              # run the two-round review loop on `outputs`
    gate_items_file: str | None = None                # JSON of choices to surface at the next human gate
    # check / compare
    command: list[str] = field(default_factory=list)
    fix_rounds: int = 2
    left: str = ""
    right: str = ""
    key: list[str] = field(default_factory=list)
    key_from: str = ""                                # JSON file holding the key columns, if `key` is empty
    tolerance: float = 0.0
    # planted_bugs
    layers: list[str] = field(default_factory=list)   # names of check/compare steps to run per bug
    bugs_file: str = ""                               # JSON list, approved by the human
    mutable: list[str] = field(default_factory=list)  # globs the planter may change
    rebuild: list[str] = field(default_factory=list)  # command run in each mutant copy before the layers
    copy_exclude: list[str] = field(default_factory=lambda: [".git", ".rlo"])
    # human
    items_from: list[str] = field(default_factory=list)  # extra gate items files to include
    recycle_rule: bool = False                        # stage 4: two recycles per claim, then a kill review
    # snapshot
    include: list[str] = field(default_factory=list)  # globs to fingerprint (outputs + definition)

    def validate(self) -> None:
        if self.kind not in STEP_KINDS:
            raise ValueError(f"step {self.name}: unknown kind {self.kind}")
        if self.kind == "task":
            if self.role not in TOOL_ROLES:
                raise ValueError(f"step {self.name}: role must be one of {TOOL_ROLES}")
            if not self.prompt:
                raise ValueError(f"step {self.name}: task needs a prompt")
        if self.kind == "check" and not self.command:
            raise ValueError(f"step {self.name}: check needs a command")
        if self.kind == "compare" and not (self.left and self.right and (self.key or self.key_from)):
            raise ValueError(f"step {self.name}: compare needs left, right and key or key_from")
        if self.kind == "planted_bugs" and not (self.layers and self.bugs_file and self.mutable):
            raise ValueError(f"step {self.name}: planted_bugs needs layers, bugs_file and mutable")
        if self.kind == "snapshot" and not self.include:
            raise ValueError(f"step {self.name}: snapshot needs include")


@dataclass
class StageConfig:
    name: str
    title: str
    gate_no: int
    steps: list[Step]
    reviewer_prompt: str = "reviewer.md"
    judge_prompt: str = "judge.md"
    review_rounds: int = 2
    budget: Budget = field(default_factory=Budget)
    models: dict[str, str] = field(default_factory=dict)

    def step(self, name: str) -> Step:
        for s in self.steps:
            if s.name == name:
                return s
        raise KeyError(f"stage {self.name} has no step {name}")

    def prompt_text(self, name: str, variable: str = "") -> str:
        text = (PROMPTS_DIR / name).read_text(encoding="utf-8")
        return text.replace("{{variable}}", variable)

    def model(self, role: str) -> str:
        defaults = {
            "author": "claude-opus-5-5", "judge": "claude-opus-5-5", "planter": "claude-sonnet-5-5",
            "reviewer": "gpt-5", "builder": "gpt-5",
        }
        return self.models.get(role, defaults[role])


def _substitute(obj, variable: str):
    if isinstance(obj, str):
        return obj.replace("{{variable}}", variable)
    if isinstance(obj, list):
        return [_substitute(x, variable) for x in obj]
    if isinstance(obj, dict):
        return {k: _substitute(v, variable) for k, v in obj.items()}
    return obj


def load_stage(name: str, variable: str = "{{variable}}", stages_dir: Path = STAGES_DIR) -> StageConfig:
    """Load a stage; `{{variable}}` in any string field becomes the variable name."""
    path = stages_dir / f"{name}.toml"
    if not path.exists():
        raise FileNotFoundError(f"no stage config at {path}")
    raw = _substitute(tomllib.loads(path.read_text(encoding="utf-8")), variable)
    steps = [Step(**s) for s in raw.pop("step", [])]
    for s in steps:
        s.validate()
    names = [s.name for s in steps]
    if len(names) != len(set(names)):
        raise ValueError(f"stage {name}: duplicate step names")
    budget = Budget(**raw.pop("budget", {}))
    models = raw.pop("models", {})
    return StageConfig(name=name, steps=steps, budget=budget, models=models, **raw)
