"""Tools the author model may use. All paths are confined to the target repository."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


class ToolError(Exception):
    pass


ALLOWED_COMMANDS = ("Rscript", "python", "python3")


class Sandbox:
    def __init__(self, target: Path, readable: list[str], tool_counter=None):
        self.target = Path(target).resolve()
        self.readable = readable
        self.tool_calls = 0

    # -- path safety -----------------------------------------------------
    def _resolve(self, rel: str) -> Path:
        p = (self.target / rel).resolve()
        if self.target not in p.parents and p != self.target:
            raise ToolError(f"path escapes the target repository: {rel}")
        return p

    # -- tools ------------------------------------------------------------
    def list_files(self, pattern: str = "**/*") -> str:
        self.tool_calls += 1
        files = [
            str(p.relative_to(self.target))
            for p in sorted(self.target.glob(pattern))
            if p.is_file() and ".git" not in p.parts and ".rlo" not in p.parts
        ]
        return "\n".join(files[:500])

    def read_file(self, path: str) -> str:
        self.tool_calls += 1
        p = self._resolve(path)
        if not p.exists():
            raise ToolError(f"no such file: {path}")
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

    def run_command(self, program: str, args: list[str], timeout_s: int = 600) -> str:
        self.tool_calls += 1
        if program not in ALLOWED_COMMANDS:
            raise ToolError(f"program not allowed: {program}; allowed: {ALLOWED_COMMANDS}")
        for a in args:
            if a.startswith("/") or a.startswith("..") or "~" in a:
                raise ToolError(f"argument looks like it leaves the repository: {a}")
        try:
            r = subprocess.run(
                [program, *args], cwd=self.target, capture_output=True, text=True, timeout=timeout_s
            )
        except FileNotFoundError:
            raise ToolError(f"{program} is not installed on this machine")
        except subprocess.TimeoutExpired:
            raise ToolError(f"{program} timed out after {timeout_s}s")
        out = {"returncode": r.returncode, "stdout": r.stdout[-20_000:], "stderr": r.stderr[-20_000:]}
        return json.dumps(out)

    # -- dispatch ----------------------------------------------------------
    def dispatch(self, name: str, inp: dict) -> str:
        fn = {
            "list_files": self.list_files,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "run_command": self.run_command,
        }.get(name)
        if fn is None:
            raise ToolError(f"unknown tool {name}")
        return fn(**inp)


TOOL_DEFINITIONS = [
    {
        "name": "list_files",
        "description": "List files in the target repository matching a glob pattern (default all).",
        "input_schema": {
            "type": "object",
            "properties": {"pattern": {"type": "string"}},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "read_file",
        "description": "Read a text file from the target repository. Path is relative to the repository root.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "write_file",
        "description": "Write a text file inside the target repository, creating folders as needed.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "run_command",
        "description": "Run Rscript or python inside the target repository with the given arguments. Returns JSON with returncode, stdout, stderr.",
        "input_schema": {
            "type": "object",
            "properties": {
                "program": {"type": "string", "enum": list(ALLOWED_COMMANDS)},
                "args": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["program", "args"],
            "additionalProperties": False,
        },
    },
]
