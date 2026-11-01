"""The subscription adapters, driven by stand-in executables that speak the real programs' output shapes."""

import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

from rlo.calls import CallLog
from rlo.models.base import Finding
from rlo.models.cli import ClaudeCLIAgent, ClaudeCLIJudge, CodexCLIReviewer, _claude_result_text

FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, re, sys, os
stdin = sys.stdin.read()
args = sys.argv[1:]
# behave like `claude -p ... --output-format json`: write the requested record to the file named in the prompt
m = re.search(r"write it to the file (\S+\.json)", stdin)
record = {"summary": "fake claude did the task", "files_written": ["spec/x.md"]}
if "responses" in stdin and "verdict" in stdin and "findings" not in stdin.split("schema")[0]:
    record = {"summary": "answered", "responses": [{"id": "F1", "verdict": "reject", "change": "", "reason": "no"}]}
if "winner" in stdin:
    record = {"winner": "B", "reason": "B cites the definition"}
if m and "--add-dir" in args and "--nofile" not in args:
    open(m.group(1), "w").write(json.dumps(record))
    result = "done, record written"
else:
    result = "```json\n" + json.dumps(record) + "\n```"
print(json.dumps({"type": "result", "subtype": "success", "result": result, "session_id": "s1", "total_cost_usd": 0}))
'''

FAKE_CODEX = r'''#!/usr/bin/env python3
import json, sys
args = sys.argv[1:]
stdin = sys.stdin.read()
out = args[args.index("-o") + 1]
if "matches_claim" in stdin:
    msg = {"matches_claim": True, "reason": "the copy drops the window filter"}
else:
    msg = {"findings": [{"id": "F1", "severity": "high", "kind": "error", "claim": "c", "evidence": "e",
                         "proposed_fix": "p", "checkable_by": "test"}]}
open(out, "w").write("Here is my review:\n```json\n" + json.dumps(msg) + "\n```")
print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}}))
'''


def _exe(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class CLIAdapters(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        _exe(self.bin / "fake_claude.py", FAKE_CLAUDE)
        _exe(self.bin / "fake_codex.py", FAKE_CODEX)
        self.settings = {
            "claude": {"command": [sys.executable, str(self.bin / "fake_claude.py")], "tool_args": ["-p", "--output-format", "json"],
                       "judge_args": ["-p", "--output-format", "json", "--max-turns", "1"], "model_flag": "--model",
                       "max_turns_flag": "--max-turns", "timeout_s": 60},
            "codex": {"command": [sys.executable, str(self.bin / "fake_codex.py")], "args": ["exec", "--json"], "model_flag": "--model",
                      "last_message_flag": "-o", "output_schema_flag": "", "timeout_s": 60},
        }
        self.calls = CallLog(self.root / "calls")
        self.work = self.root / "work"
        self.work.mkdir()
        self.ctx = {"stage": "s", "variable": "v", "step": "t", "round": 1}

    def tearDown(self):
        self.tmp.cleanup()

    def test_claude_agent_reads_record_file(self):
        agent = ClaudeCLIAgent("claude-opus-5-5", self.calls, "sys", "author", 20, self.settings, self.root / "out")
        r = agent.run_task("do it", self.work, self.ctx)
        self.assertEqual(r.files_written, ["spec/x.md"])
        rec = self.calls.all()[-1]
        self.assertEqual(rec.provider, "claude-cli")
        self.assertIn("--max-turns", rec.request["command"])
        self.assertIn("20", rec.request["command"])

    def test_claude_agent_falls_back_to_result_text(self):
        s = json.loads(json.dumps(self.settings))
        s["claude"]["tool_args"] = ["-p", "--nofile"]  # the stand-in then prints the record in its result text
        agent = ClaudeCLIAgent("m", self.calls, "sys", "author", 5, s, self.root / "out")
        r = agent.run_task("do it", self.work, self.ctx)
        self.assertEqual(r.summary, "fake claude did the task")

    def test_claude_judge(self):
        j = ClaudeCLIJudge("m", self.calls, "sys", self.settings, self.work)
        f = Finding(id="F1", severity="high", kind="error", claim="c", evidence="e", proposed_fix="p")
        v = j.judge(f, "A says", "B says", self.ctx)
        self.assertEqual(v.winner, "B")

    def test_codex_reviewer_and_confirm(self):
        rv = CodexCLIReviewer("gpt-5", self.calls, "sys", self.work, self.settings)
        fs = rv.review({"spec/x.md": "text"}, {**self.ctx, "task": "t"})
        self.assertEqual([f.id for f in fs], ["F1"])
        ok, why = rv.confirm_mutant(fs[0], "--- a\n+++ b\n", self.ctx)
        self.assertTrue(ok)
        rec = self.calls.all()[-1]
        self.assertEqual(rec.provider, "codex-cli")
        self.assertEqual(rec.request["command"][-1], "-")

    def test_result_text_shapes(self):
        self.assertEqual(_claude_result_text(json.dumps({"type": "result", "result": "x"})), "x")
        self.assertEqual(_claude_result_text(json.dumps([{"type": "system"}, {"type": "result", "result": "y"}])), "y")
        self.assertEqual(_claude_result_text("plain"), "plain")


if __name__ == "__main__":
    unittest.main()
