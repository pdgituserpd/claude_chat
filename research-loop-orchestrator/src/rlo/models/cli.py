"""Subscription adapters: Claude Code and Codex as command-line programs.

Claude Code (`claude -p`) runs under a Claude subscription; Codex (`codex exec`) under a
ChatGPT subscription. Each call is a fresh, non-interactive session started in a work
folder. The prompt goes in on standard input; the program's full output is saved as the raw
call record; the structured record is read from a file the agent writes, or extracted from
its last message.

Flags differ between versions of both programs. The defaults below are overridden by
`cli_settings.toml` at the orchestrator root. Nothing here is exercised against the real
programs in this repository's tests; the tests use stand-in executables that speak the same
output format.
"""

from __future__ import annotations

import json
import os
import subprocess
import tomllib
import uuid
from pathlib import Path

from ..calls import CallLog
from ..config import PKG_ROOT
from .base import (CONFIRM_SCHEMA, FINDINGS_SCHEMA, RESPONSES_SCHEMA, SUMMARY_SCHEMA, TEST_PLAN_SCHEMA,
                   VERDICT_SCHEMA, Finding, FindingResponse, JudgeVerdict, TaskResult, TestPlan, extract_json)
from .prompts import (bundle_artifacts, confirm_prompt, judge_prompt, plan_test_prompt, record_instruction,
                      rereview_prompt, respond_prompt, review_prompt)

DEFAULT_SETTINGS = {
    "claude": {
        "command": ["claude"],
        "tool_args": ["-p", "--output-format", "json", "--permission-mode", "acceptEdits",
                      "--allowedTools", "Read,Write,Edit,Glob,Grep,Bash(Rscript:*),Bash(python:*),Bash(python3:*)"],
        "judge_args": ["-p", "--output-format", "json", "--max-turns", "1"],
        "model_flag": "--model",
        "max_turns_flag": "--max-turns",
        "timeout_s": 3600,
    },
    "codex": {
        "command": ["codex"],
        "args": ["exec", "--sandbox", "read-only", "--skip-git-repo-check", "--json"],
        "model_flag": "--model",
        "last_message_flag": "-o",
        "output_schema_flag": "",   # set to "--output-schema" if your Codex version supports it
        "timeout_s": 1800,
    },
}


def load_settings(path: Path | None = None) -> dict:
    path = path or (PKG_ROOT / "cli_settings.toml")
    settings = json.loads(json.dumps(DEFAULT_SETTINGS))
    if path.exists():
        user = tomllib.loads(path.read_text(encoding="utf-8"))
        for k, v in user.items():
            settings.setdefault(k, {}).update(v)
    return settings


def _run(cmd: list[str], cwd: Path, stdin_text: str, timeout_s: int) -> dict:
    try:
        r = subprocess.run(cmd, cwd=cwd, input=stdin_text, capture_output=True, text=True, timeout=timeout_s,
                           env=dict(os.environ))
    except FileNotFoundError:
        raise RuntimeError(f"{cmd[0]} is not installed or not on PATH")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"{cmd[0]} timed out after {timeout_s}s")
    return {"returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr[-20_000:]}


def _claude_result_text(stdout: str) -> str:
    """`--output-format json` prints one JSON object with a `result` field."""
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return stdout
    if isinstance(data, dict):
        return str(data.get("result", ""))
    if isinstance(data, list):  # some versions print the event list
        for ev in reversed(data):
            if isinstance(ev, dict) and ev.get("type") == "result":
                return str(ev.get("result", ""))
    return stdout


class ClaudeCLIAgent:
    """Author, builder or planter through Claude Code's non-interactive mode."""

    provider = "claude-cli"
    family = "anthropic"

    def __init__(self, model: str, calls: CallLog, system_prompt: str, role: str, max_tool_calls: int,
                 settings: dict | None = None, out_dir: Path | None = None):
        self.model = model
        self.calls = calls
        self.system = system_prompt
        self.role = role
        self.max_tool_calls = max_tool_calls
        self.s = (settings or load_settings())["claude"]
        self.out_dir = Path(out_dir) if out_dir else None

    def _invoke(self, role: str, prompt: str, workdir: Path, context: dict, schema: dict) -> dict:
        workdir = Path(workdir)
        out_dir = self.out_dir or (workdir / ".rlo_out")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{uuid.uuid4().hex[:10]}.json"
        full = self.system + "\n\n" + prompt + record_instruction(schema, str(out_path))
        cmd = [*self.s["command"], *self.s["tool_args"], self.s["model_flag"], self.model,
               self.s["max_turns_flag"], str(self.max_tool_calls), "--add-dir", str(out_dir),
               "Carry out the task given on standard input."]
        r = _run(cmd, workdir, full, self.s["timeout_s"])
        self.calls.record(role=role, provider=self.provider, model=self.model, stage=context["stage"],
                          variable=context["variable"], round=context.get("round", 0),
                          request={"command": cmd, "stdin": full[:5000]}, response=r,
                          meta={"out_path": str(out_path)})
        if r["returncode"] != 0:
            raise RuntimeError(f"claude exited {r['returncode']}: {r['stderr'][-500:]}")
        if out_path.exists():
            return json.loads(out_path.read_text(encoding="utf-8"))
        return json.loads(extract_json(_claude_result_text(r["stdout"])))

    def run_task(self, task, workdir, context) -> TaskResult:
        data = self._invoke(self.role, task, workdir, context, SUMMARY_SCHEMA)
        return TaskResult(summary=data["summary"], files_written=list(data.get("files_written", [])), raw=data)

    def respond(self, findings, workdir, context) -> TaskResult:
        data = self._invoke(self.role, respond_prompt(findings), workdir, context, RESPONSES_SCHEMA)
        responses = []
        for r in data["responses"]:
            fr = FindingResponse(**r)
            fr.validate()
            responses.append(fr)
        return TaskResult(summary=data["summary"], responses=responses, raw=data)

    def plan_test(self, finding, workdir, context) -> TestPlan | None:
        data = self._invoke("test", plan_test_prompt(finding), workdir, context, TEST_PLAN_SCHEMA)
        return TestPlan(finding_id=finding.id, **data)


class ClaudeCLIJudge:
    provider = "claude-cli"
    family = "anthropic"

    def __init__(self, model: str, calls: CallLog, system_prompt: str, settings: dict | None = None,
                 scratch: Path | None = None):
        self.model = model
        self.calls = calls
        self.system = system_prompt
        self.s = (settings or load_settings())["claude"]
        self.scratch = scratch

    def judge(self, finding, position_a, position_b, context) -> JudgeVerdict:
        full = self.system + "\n\n" + judge_prompt(finding, position_a, position_b) + record_instruction(VERDICT_SCHEMA, None)
        cmd = [*self.s["command"], *self.s["judge_args"], self.s["model_flag"], self.model,
               "Answer the question given on standard input."]
        cwd = self.scratch or Path.cwd()
        r = _run(cmd, cwd, full, self.s["timeout_s"])
        self.calls.record(role="judge", provider=self.provider, model=self.model, stage=context["stage"],
                          variable=context["variable"], round=context.get("round", 0),
                          request={"command": cmd, "finding": finding.id, "A": position_a, "B": position_b}, response=r)
        if r["returncode"] != 0:
            raise RuntimeError(f"claude exited {r['returncode']}: {r['stderr'][-500:]}")
        data = json.loads(extract_json(_claude_result_text(r["stdout"])))
        return JudgeVerdict(finding_id=finding.id, winner=data["winner"], reason=data["reason"])


class CodexCLIReviewer:
    """Reviewer through Codex's non-interactive mode, read-only sandbox, started in an empty folder
    so it sees only what the prompt carries."""

    provider = "codex-cli"
    family = "openai"

    def __init__(self, model: str, calls: CallLog, system_prompt: str, scratch: Path, settings: dict | None = None):
        self.model = model
        self.calls = calls
        self.system = system_prompt
        self.scratch = Path(scratch)
        self.s = (settings or load_settings())["codex"]

    def _invoke(self, prompt: str, schema: dict, rnd: int, context: dict) -> dict:
        cwd = self.scratch / f"codex_{uuid.uuid4().hex[:8]}"
        cwd.mkdir(parents=True, exist_ok=True)
        last = cwd / "last_message.txt"
        cmd = [*self.s["command"], *self.s["args"], self.s["model_flag"], self.model, self.s["last_message_flag"], str(last)]
        if self.s.get("output_schema_flag"):
            schema_path = cwd / "schema.json"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            cmd += [self.s["output_schema_flag"], str(schema_path)]
        cmd.append("-")  # prompt on standard input
        full = self.system + "\n\n" + prompt + record_instruction(schema, None)
        r = _run(cmd, cwd, full, self.s["timeout_s"])
        text = last.read_text(encoding="utf-8") if last.exists() else r["stdout"]
        self.calls.record(role="reviewer", provider=self.provider, model=self.model, stage=context["stage"],
                          variable=context["variable"], round=rnd,
                          request={"command": cmd, "stdin": full[:5000]}, response={**r, "last_message": text[:20_000]})
        if r["returncode"] != 0:
            raise RuntimeError(f"codex exited {r['returncode']}: {r['stderr'][-500:]}")
        return json.loads(extract_json(text))

    def review(self, artifacts, context) -> list[Finding]:
        data = self._invoke(review_prompt(context.get("task", ""), bundle_artifacts(artifacts)), FINDINGS_SCHEMA, 1, context)
        return [Finding.from_dict(d) for d in data["findings"]]

    def rereview(self, artifacts, rejected, context) -> list[Finding]:
        data = self._invoke(rereview_prompt(rejected, bundle_artifacts(artifacts)), FINDINGS_SCHEMA, 2, context)
        return [Finding.from_dict(d) for d in data["findings"]]

    def confirm_mutant(self, finding, diff, context) -> tuple[bool, str]:
        data = self._invoke(confirm_prompt(finding, diff), CONFIRM_SCHEMA, context.get("round", 0), context)
        return bool(data["matches_claim"]), data["reason"]
