"""Stage 2 end to end with canned models: define, review, dispute routing, gate, approve, apply, snapshot."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from rlo.cli import main
from rlo.config import PKG_ROOT

FIX = PKG_ROOT / "tests" / "fixtures" / "stage2.json"
FIX_BAD = PKG_ROOT / "tests" / "fixtures" / "stage2_bad_mutant.json"
TARGET_MIN = PKG_ROOT / "examples" / "target_min"


def fill(text: str, choices: dict) -> str:
    for cid, choice in choices.items():
        i = text.index(f"## {cid}:")
        j = text.index("Choice: ", i)
        text = text[:j] + f"Choice: {choice}" + text[j + len("Choice: "):]
    return text


class Stage2(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.target = Path(self.tmp) / "target"
        shutil.copytree(TARGET_MIN, self.target)
        self.common = ["--target", str(self.target), "--stage", "stage2_measures", "--variable", "new_classes"]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def state(self):
        return json.loads((self.target / ".rlo" / "state_stage2_measures_new_classes.json").read_text())

    def jsonl(self, name):
        p = self.target / "logs" / name
        return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []

    def test_full_pass(self):
        rc = main(["run", *self.common, "--mode", "fixtures", "--fixture", str(FIX), "--seed", "1"])
        self.assertEqual(rc, 0)
        st = self.state()
        self.assertEqual(st["status"], "waiting_human")
        self.assertEqual(st["current_step"], "gate2")
        self.assertEqual(st["steps_done"], ["define"])
        gate = self.target / st["gate_file"]
        text = gate.read_text()
        for needle in ("## C1:", "## C2:", "## C3:", "## KEY:", "## DISPUTE-F3:", "## SIGNOFF-gate2:"):
            self.assertIn(needle, text)
        self.assertNotIn("## DISPUTE-F2", text)   # settled by the coded test
        self.assertNotIn("## DISPUTE-F4", text)   # settled by the blinded judge, then accepted
        self.assertIn("AI default: filing year", text)            # direct precedent: default shown
        self.assertEqual(text.count("(none: no direct precedent"), 5)  # C2, C3, KEY, DISPUTE-F3, SIGNOFF

        disputes = {d["finding"]["id"]: d for d in self.jsonl("dispute_log.jsonl")}
        self.assertEqual(disputes["F2"]["route"], "test")
        self.assertEqual(disputes["F2"]["outcome"], "author")
        t = disputes["F2"]["detail"]["test"]
        self.assertTrue(t["mutant_failed"] and t["subject_passed"] and t["valid"] and t["reviewer_confirmed"])
        self.assertTrue((self.target / "tests" / "dispute_F2.py").exists())
        self.assertEqual(disputes["F3"]["route"], "human")
        self.assertEqual(disputes["F4"]["route"], "judge")
        self.assertIn(disputes["F4"]["judge_sided_with_own_family"], (True, False))

        roles = sorted({json.loads(c.read_text())["role"] for c in (self.target / ".rlo" / "calls").glob("*.json")})
        self.assertEqual(roles, ["author", "judge", "reviewer", "test"])

        # second run refuses; approve refuses while empty
        with self.assertRaises(RuntimeError):
            main(["run", *self.common, "--mode", "fixtures", "--fixture", str(FIX)])
        self.assertEqual(main(["approve", *self.common, "--mode", "fixtures", "--fixture", str(FIX)]), 2)

        gate.write_text(fill(text, {"C1": "grant year", "C2": "all listed", "C3": "300", "KEY": "key",
                                    "DISPUTE-F3": "author", "SIGNOFF-gate2": "approve"}))
        rc = main(["approve", *self.common, "--mode", "fixtures", "--fixture", str(FIX), "--by", "Pouya"])
        self.assertEqual(rc, 0)
        st = self.state()
        self.assertEqual(st["status"], "done")
        self.assertEqual(st["steps_done"], ["define", "gate2", "apply_decisions", "snapshot"])
        self.assertIn("[D001]", (self.target / "spec" / "new_classes_definition.md").read_text())

        ds = {d["gate_item_id"]: d for d in self.jsonl("decision_log.jsonl")}
        self.assertEqual(ds["C1"]["outcome"], "overruled_default")
        self.assertEqual(ds["C2"]["outcome"], "chose")
        self.assertIsNone(ds["C2"]["ai_default"])
        self.assertEqual(ds["C2"]["precedent_type"], "closest")
        self.assertEqual(ds["DISPUTE-F3"]["source"], "dispute")
        j = self.jsonl("judgment_log.jsonl")[0]
        self.assertEqual((j["accepted_default"], j["overruled_default"], j["chose"]), (0, 1, 5))
        self.assertEqual(j["gate"], 2)
        runs = self.jsonl("run_log.jsonl")
        self.assertEqual([r["kind"] for r in runs], ["task:define", "task:apply_decisions", "snapshot"])
        self.assertIn("software_versions", runs[0])
        self.assertTrue((self.target / ".rlo" / "snapshots" / "stage2_measures_new_classes.json").exists())

    def test_bad_mutant_sends_dispute_to_human(self):
        main(["run", *self.common, "--mode", "fixtures", "--fixture", str(FIX_BAD), "--seed", "1"])
        text = (self.target / self.state()["gate_file"]).read_text()
        self.assertIn("## DISPUTE-F2:", text)
        self.assertIn("test did not fail on the mutant", text)
        d = {d["finding"]["id"]: d for d in self.jsonl("dispute_log.jsonl")}["F2"]
        self.assertEqual(d["route"], "human")
        self.assertFalse(d["detail"]["test"]["valid"])

    def test_reset_then_rerun(self):
        main(["run", *self.common, "--mode", "fixtures", "--fixture", str(FIX), "--seed", "1"])
        self.assertEqual(main(["reset", *self.common]), 0)
        self.assertEqual(main(["run", *self.common, "--mode", "fixtures", "--fixture", str(FIX), "--seed", "2"]), 0)
        self.assertEqual(len(self.jsonl("run_log.jsonl")), 2)  # records are kept across resets


class ManualModeResumes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.target = Path(self.tmp) / "target"
        shutil.copytree(TARGET_MIN, self.target)
        self.common = ["--target", str(self.target), "--stage", "stage2_measures", "--variable", "nc"]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def state(self):
        return json.loads((self.target / ".rlo" / "state_stage2_measures_nc.json").read_text())

    def test_hand_offs(self):
        fx = json.loads(FIX.read_text())
        # 1. author's task -> bundle written, waiting
        self.assertEqual(main(["run", *self.common, "--mode", "manual"]), 0)
        st = self.state()
        self.assertEqual(st["status"], "waiting_manual")
        bundle = self.target / st["manual_file"]
        self.assertTrue(bundle.exists() and "author / task" in bundle.read_text())
        # the human does the work in a chat window and saves the files; ingest validates the reply
        for rel, content in fx["tasks"]["define"]["writes"].items():
            p = self.target / rel.replace("new_classes", "nc")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content.replace("new_classes", "nc"))
        reply = Path(self.tmp) / "reply.json"
        reply.write_text('Here you go:\n```json\n{"summary": "done by hand", "files_written": ["spec/nc_definition.md"]}\n```')
        self.assertEqual(main(["ingest", *self.common, "--file", str(reply)]), 0)
        bad = Path(self.tmp) / "bad.json"
        bad.write_text('{"nope": 1}')
        # 2. resume -> reviewer's turn
        self.assertEqual(main(["run", *self.common, "--mode", "manual"]), 0)
        st = self.state()
        self.assertEqual(st["status"], "waiting_manual")
        self.assertIn("reviewer / review", (self.target / st["manual_file"]).read_text())
        self.assertEqual(main(["ingest", *self.common, "--file", str(bad)]), 2)
        reply.write_text('{"findings": []}')
        self.assertEqual(main(["ingest", *self.common, "--file", str(reply)]), 0)
        # 3. resume -> no findings, straight to the gate; the author's task was not asked again
        self.assertEqual(main(["run", *self.common, "--mode", "manual"]), 0)
        st = self.state()
        self.assertEqual(st["status"], "waiting_human")
        bundles = sorted(p.name for p in (self.target / ".rlo" / "manual").glob("*.md"))
        self.assertEqual(len(bundles), 2)
        calls = [json.loads(c.read_text()) for c in (self.target / ".rlo" / "calls").glob("*.json")]
        self.assertEqual(sorted(c["provider"] for c in calls), ["manual", "manual"])


if __name__ == "__main__":
    unittest.main()
