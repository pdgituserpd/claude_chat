"""Tools the tool-using roles may use through the API adapters. Paths are confined to a work folder.

The same Sandbox runs the check commands for the engine, so every command the system runs
goes through one place with one allow-list.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


class ToolError(Exception):
    pass


ALLOWED_COMMANDS = ("Rscript", "python", "python3")


def resolve_program(program: str) -> str:
    """`python` in a config means the interpreter running the orchestrator, on every OS."""
    if program in ("python", "python3"):
        return sys.executable
    return program


def run_command(workdir: Path, command: list[str], timeout_s: int = 1800, env: dict | None = None) -> dict:
    if not command:
        raise ToolError("empty command")
    program, args = command[0], command[1:]
    if program not in ALLOWED_COMMANDS:
        raise ToolError(f"program not allowed: {program}; allowed: {ALLOWED_COMMANDS}")
    for a in args:
        if a.startswith("/") or a.startswith("..") or "~" in a or ":\\" in a:
            raise ToolError(f"argument looks like it leaves the work folder: {a}")
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    try:
        r = subprocess.run(
            [resolve_program(program), *args], cwd=workdir, capture_output=True, text=True,
            timeout=timeout_s, env=full_env,
        )
    except FileNotFoundError:
        raise ToolError(f"{program} is not installed on this machine")
    except subprocess.TimeoutExpired:
        raise ToolError(f"{program} timed out after {timeout_s}s")
    return {"returncode": r.returncode, "stdout": r.stdout[-20_000:], "stderr": r.stderr[-20_000:]}


def files_matching(root: Path, globs: list[str]) -> list[Path]:
    root = Path(root)
    out: list[Path] = []
    seen = set()
    for g in globs:
        for p in sorted(root.glob(g)):
            rel = p.relative_to(root).parts
            if p.is_file() and ".git" not in rel and ".rlo" not in rel and p not in seen:
                seen.add(p)
                out.append(p)
    return out


class Sandbox:
    def __init__(self, workdir: Path, readable: list[str] | None = None):
        self.workdir = Path(workdir).resolve()
        self.readable = list(readable or [])
        self.tool_calls = 0

    def _resolve(self, rel: str) -> Path:
        p = (self.workdir / rel).resolve()
        if self.workdir not in p.parents and p != self.workdir:
            raise ToolError(f"path escapes the work folder: {rel}")
        return p

    def _may_read(self, p: Path) -> bool:
        if not self.readable:
            return True
        return p in set(files_matching(self.workdir, self.readable))

    def list_files(self, pattern: str = "**/*") -> str:
        self.tool_calls += 1
        files = [p for p in files_matching(self.workdir, [pattern]) if self._may_read(p)]
        return "\n".join(str(p.relative_to(self.workdir)) for p in files[:500])

    def read_file(self, path: str) -> str:
        self.tool_calls += 1
        p = self._resolve(path)
        if not p.exists():
            raise ToolError(f"no such file: {path}")
        if not self._may_read(p):
            raise ToolError(f"not readable in this step: {path}")
        data = p.read_text(encoding="utf-8", errors="replace")
        if len(data) > 200_000:
            raise ToolError(f"{path} is too large to read whole ({len(data)} chars); read a narrower file")
        return data

    def write_file(self, path: str, content: str) -> str:
        self.tool_calls += 1
        p = self._resolve(path)
        if ".git" in p.parts or ".rlo" in p.parts:
            raise ToolError("may not write into .git or .rlo")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"wrote {len(content)} chars to {path}"

    def run(self, program: str, args: list[str]) -> str:
        self.tool_calls += 1
        return json.dumps(run_command(self.workdir, [program, *args], timeout_s=600))

    def dispatch(self, name: str, inp: dict) -> str:
        fn = {"list_files": self.list_files, "read_file": self.read_file,
              "write_file": self.write_file, "run_command": self.run}.get(name)
        if fn is None:
            raise ToolError(f"unknown tool {name}")
        return fn(**inp)


TOOL_DEFINITIONS = [
    {"name": "list_files", "description": "List files in the work folder matching a glob pattern (default all).",
     "input_schema": {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": [], "additionalProperties": False}},
    {"name": "read_file", "description": "Read a text file from the work folder. Path is relative to its root.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": False}},
    {"name": "write_file", "description": "Write a text file inside the work folder, creating folders as needed.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                      "required": ["path", "content"], "additionalProperties": False}},
    {"name": "run_command", "description": "Run Rscript or python inside the work folder. Returns JSON with returncode, stdout, stderr.",
     "input_schema": {"type": "object", "properties": {"program": {"type": "string", "enum": list(ALLOWED_COMMANDS)},
                      "args": {"type": "array", "items": {"type": "string"}}}, "required": ["program", "args"], "additionalProperties": False}},
]
