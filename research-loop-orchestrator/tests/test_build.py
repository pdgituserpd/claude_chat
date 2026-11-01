"""The build stage on a Python stand-in: blind rebuild in an isolated folder, comparisons, a failing
check the author fixes, planted bugs with a catch matrix, the worked-case gate, the snapshot."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from rlo.calls import CallLog
from rlo.cli import build_roles
from rlo.config import PKG_ROOT, load_stage
from rlo.engine import Engine, approve_stage
from rlo.state import Store
from tests.test_stage2 import fill

FIX = PKG_ROOT / "tests" / "fixtures" / "build.json"
TARGET = PKG_ROOT / "examples" / "target_build"
STAGES = PKG_ROOT / "tests" / "stages"


class BuildStage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.target = Path(self.tmp) / "t"
        shutil.copytree(TARGET, self.target)
        self.cfg = load_stage("build_test", "x", stages_dir=STAGES)
        self.store = Store(self.target)
        self.calls = CallLog(self.store.calls_dir)
        self.roles = build_roles("fixtures", self.cfg, self.store, self.calls, str(FIX))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def jsonl(self, name):
        return self.store.read_jsonl(name)

    def run_engine(self):
        return Engine(self.cfg, "x", self.roles, self.store, self.calls).run()

    def test_whole_stage(self):
        st = self.run_engine()
        # 1. paused for the planted-bug approval
        self.assertEqual(st.status, "waiting_human")
        self.assertEqual(st.current_step, "planted_bugs")
        done = st.steps_done
        self.assertEqual(done, ["fast_build", "slow_build", "blind_rebuild", "write_checks", "rules", "compare_fast_slow", "compare_fast_blind"])
        # blind rebuild ran in an isolated folder holding only the definition, keys and data, then copied back
        iso = self.store.work_dir / "build_test_x_blind_rebuild"
        self.assertTrue((iso / "spec" / "x_definition.md").exists())
        self.assertFalse((iso / "code").exists() and any((iso / "code").iterdir()))
        self.assertTrue((self.target / "output" / "x_blind.csv").exists())
        # the rules check failed once (duplicate keys) and the author fixed it
        runs = self.jsonl("run_log.jsonl")
        rule_runs = [r for r in runs if r["kind"] == "check:rules"]
        self.assertEqual([r["checks"]["ok"] for r in rule_runs], [False, True])
        self.assertEqual(rule_runs[1]["checks"]["attempt"], 1)
        cmp_ = [r for r in runs if r["kind"] == "compare:compare_fast_slow"][0]
        self.assertTrue(cmp_["checks"]["ok"])
        self.assertTrue((self.store.report_dir / "compare_x_compare_fast_slow.json").exists())
        gate = self.target / st.gate_file
        text = gate.read_text()
        self.assertIn("## PLANTED-BUGS-planted_bugs:", text)
        self.assertNotIn("SIGNOFF", text)  # not a human step: no sign-off item
        gate.write_text(fill(text, {"PLANTED-BUGS-planted_bugs": "approve"}))
        out = approve_stage(cfg=self.cfg, store=self.store, variable="x", decided_by="Pouya")
        self.assertEqual(out["status"], "running")
        self.assertEqual(self.jsonl("decision_log.jsonl")[-1]["source"], "system")

        # 2. the bugs run; B1 caught by the comparison, B2 escapes everything, author tries a fix, still escapes
        st = self.run_engine()
        self.assertEqual(st.status, "waiting_human")
        self.assertEqual(st.current_step, "worked_case")
        matrix = json.loads((self.store.report_dir / "catch_matrix_x.json").read_text())
        self.assertTrue(matrix["results"]["B1"]["caught"]["compare_fast_slow"])
        self.assertFalse(matrix["results"]["B1"]["caught"]["rules"])
        self.assertFalse(matrix["results"]["B1"]["caught"]["ai_review"])
        self.assertFalse(any(matrix["results"]["B2"]["caught"].values()))
        self.assertEqual(matrix["results"]["B1"]["files_changed"], ["code/x_fast.py"])
        md = (self.store.report_dir / "catch_matrix_x.md").read_text()
        self.assertIn("| B1 | visible only in the data | yes | no | no | 1 |", md)
        self.assertIn("Escaped: B2", md)
        bugs = json.loads((self.target / "report" / "x_planted_bugs.json").read_text())
        self.assertEqual(bugs["approved_by"], "Pouya")
        # the real repo was not touched by the planting
        self.assertNotIn("* 3", (self.target / "code" / "x_fast.py").read_text())
        text = (self.target / st.gate_file).read_text()
        self.assertIn("## ESCAPED-B2:", text)
        self.assertIn("## SIGNOFF-worked_case:", text)
        (self.target / st.gate_file).write_text(fill(text, {"ESCAPED-B2": "accept the risk", "SIGNOFF-worked_case": "approve"}))
        out = approve_stage(cfg=self.cfg, store=self.store, variable="x", decided_by="Pouya")
        self.assertEqual(out["status"], "running")

        # 3. snapshot closes the stage
        st = self.run_engine()
        self.assertEqual(st.status, "done")
        self.assertTrue((self.store.snapshots_dir / "build_test_x.json").exists())
        self.assertEqual([r["kind"] for r in self.jsonl("run_log.jsonl")][-1], "snapshot")

    def test_signoff_stop_halts_the_stage(self):
        st = self.run_engine()
        gate = self.target / st.gate_file
        gate.write_text(fill(gate.read_text(), {"PLANTED-BUGS-planted_bugs": "revise"}))
        approve_stage(cfg=self.cfg, store=self.store, variable="x", decided_by="Pouya")
        st = self.run_engine()
        self.assertEqual(st.status, "stopped")
        self.assertIn("not approved", st.notes[-1])

    def test_resume_after_crash(self):
        """Crash while the reviewer is reading the first build. On rerun the author's task is not redone
        (its result was stored), the reviewer is asked again (its result was not), and the stage continues."""

        class Boom(Exception):
            pass

        reviewer, author = self.roles.reviewer, self.roles.author
        orig_review, orig_task = reviewer.review, author.run_task
        reviewer.review = lambda a, c: (_ for _ in ()).throw(Boom())
        with self.assertRaises(Boom):
            self.run_engine()
        st = self.store.load("build_test", "x")
        self.assertEqual(st.status, "running")
        self.assertEqual(st.steps_done, [])
        self.assertEqual(st.progress["fast_build"]["phase"], "review")
        author_steps = []

        def task_spy(task, workdir, context):
            author_steps.append(context.get("step"))
            return orig_task(task, workdir, context)

        reviewer.review = orig_review
        author.run_task = task_spy
        st = self.run_engine()
        self.assertEqual(st.current_step, "planted_bugs")
        self.assertNotIn("fast_build", author_steps)
        self.assertIn("slow_build", author_steps)


if __name__ == "__main__":
    unittest.main()
