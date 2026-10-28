"""End to end on the minimal target with fixture models: run, pause at gate 2, approve."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from rlo.cli import main
from rlo.config import PKG_ROOT

FIXTURE = PKG_ROOT / "tests" / "fixtures" / "stage2_happy.json"
TARGET_MIN = PKG_ROOT / "examples" / "target_min"


class Stage2EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.target = Path(self.tmp) / "target"
        shutil.copytree(TARGET_MIN, self.target)
        self.common = ["--target", str(self.target), "--stage", "stage2_measures", "--variable", "new_classes"]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _state(self):
        return json.loads((self.target / ".rlo" / "state_stage2_measures_new_classes.json").read_text())

    def _jsonl(self, name):
        p = self.target / "logs" / name
        return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []

    def test_run_pauses_at_gate_then_approve_logs_decisions(self):
        rc = main(["run", *self.common, "--models", "fixtures", "--fixture", str(FIXTURE), "--seed", "1"])
        self.assertEqual(rc, 0)
        st = self._state()
        self.assertEqual(st["status"], "waiting_human")
        self.assertEqual(st["round"], 2)
        gate = self.target / st["gate_file"]
        self.assertTrue(gate.exists())
        text = gate.read_text()
        # author's three open choices plus the judgment dispute F3 are on the checklist
        for needle in ("## C1:", "## C2:", "## C3:", "## DISPUTE-F3:"):
            self.assertIn(needle, text)
        self.assertNotIn("## DISPUTE-F2", text)  # settled by a coded test
        self.assertNotIn("## DISPUTE-F4", text)  # settled by the blinded judge

        # dispute log: F2 by test (author held), F3 human, F4 judge
        disputes = {d["finding"]["id"]: d for d in self._jsonl("dispute_log.jsonl")}
        self.assertEqual(disputes["F2"]["route"], "test")
        self.assertEqual(disputes["F2"]["outcome"], "author")
        self.assertEqual(disputes["F3"]["route"], "human")
        self.assertEqual(disputes["F4"]["route"], "judge")
        self.assertIn(disputes["F4"]["judge_sided_with_own_family"], (True, False))

        # every model call left a raw record
        calls = list((self.target / ".rlo" / "calls").glob("*.json"))
        roles = sorted(json.loads(c.read_text())["role"] for c in calls)
        self.assertIn("author", roles)
        self.assertIn("reviewer", roles)
        self.assertIn("judge", roles)
        self.assertIn("test", roles)

        # run log has one entry with fingerprints of spec/
        runs = self._jsonl("run_log.jsonl")
        self.assertEqual(len(runs), 1)
        self.assertIn("spec/open_choices.json", runs[0]["output_fingerprints"])

        # a second run refuses while waiting
        with self.assertRaises(RuntimeError):
            main(["run", *self.common, "--models", "fixtures", "--fixture", str(FIXTURE)])

        # approve refuses while choices are empty
        rc = main(["approve", *self.common, "--by", "Pouya"])
        self.assertEqual(rc, 2)

        # fill the checklist: keep defaults except C1, decide the dispute
        filled = text
        for cid, choice in (("C1", "grant year"), ("C2", "all listed"), ("C3", "300"), ("DISPUTE-F3", "author")):
            head = f"## {cid}:"
            i = filled.index(head)
            j = filled.index("Choice: ", i)
            filled = filled[:j] + f"Choice: {choice}" + filled[j + len("Choice: "):]
        gate.write_text(filled)

        rc = main(["approve", *self.common, "--by", "Pouya"])
        self.assertEqual(rc, 0)
        self.assertEqual(self._state()["status"], "done")
        decisions = self._jsonl("decision_log.jsonl")
        self.assertEqual([d["id"] for d in decisions], ["D001", "D002", "D003", "D004"])
        by = {d["gate_item_id"]: d for d in decisions}
        self.assertTrue(by["C1"]["overruled_default"])
        self.assertFalse(by["C2"]["overruled_default"])
        self.assertEqual(by["C1"]["decided_by"], "Pouya")
        judg = self._jsonl("judgment_log.jsonl")
        self.assertEqual(len(judg), 1)
        self.assertEqual(judg[0]["gate"], 2)
        snap = self.target / ".rlo" / "snapshots" / "stage2_measures_new_classes.json"
        self.assertTrue(snap.exists())

    def test_status_runs(self):
        self.assertEqual(main(["status", "--target", str(self.target)]), 0)


if __name__ == "__main__":
    unittest.main()


class EscalationWhenAuthorDefiesJudge(unittest.TestCase):
    def test_settled_finding_still_rejected_lands_on_gate(self):
        tmp = tempfile.mkdtemp()
        try:
            target = Path(tmp) / "target"
            shutil.copytree(TARGET_MIN, target)
            spec = json.loads(FIXTURE.read_text())
            spec["fixes"] = {"F4": {"verdict": "reject", "reason": "still disagree"}}
            fx = Path(tmp) / "fx.json"
            fx.write_text(json.dumps(spec))
            rc = main(["run", "--target", str(target), "--stage", "stage2_measures", "--variable", "v",
                       "--models", "fixtures", "--fixture", str(fx), "--seed", "3"])
            self.assertEqual(rc, 0)
            text = (target / "gates" / "stage2_measures_v.md").read_text()
            self.assertIn("## ESCALATED-F4:", text)
            st = json.loads((target / ".rlo" / "state_stage2_measures_v.json").read_text())
            self.assertTrue(any("escalated" in n for n in st["notes"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
