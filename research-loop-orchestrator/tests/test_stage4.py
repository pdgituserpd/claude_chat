"""Stage 4: the call and the two change tests reach the gate; the house rule adds a kill review after two recycles."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from rlo.cli import main
from rlo.config import PKG_ROOT
from rlo.state import Store

TARGET_MIN = PKG_ROOT / "examples" / "target_min"


class Stage4(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.target = Path(self.tmp) / "t"
        shutil.copytree(TARGET_MIN, self.target)
        choices = {"variable": "P1", "choices": [
            {"id": "CALL", "item": "The round's call", "options": ["go", "recycle", "hold", "kill"], "default": "",
             "precedent": "not stated", "precedent_type": "none", "reason": "proposal: recycle, the sample window is wrong"},
            {"id": "CHANGE-1-EITHER-WAY", "item": "Window 2001-2010: would you make it either way?", "options": ["yes", "no"],
             "default": "", "precedent": "not stated", "precedent_type": "none", "reason": ""},
            {"id": "CHANGE-1-CAN-FAIL", "item": "Window 2001-2010: can the test still fail?", "options": ["yes", "no"],
             "default": "", "precedent": "not stated", "precedent_type": "none", "reason": ""},
            {"id": "HYP-1", "item": "H1 not supported: how to report it", "options": ["report as not supported", "other"],
             "default": "report as not supported", "precedent": "the plan", "precedent_type": "direct", "reason": ""}]}
        self.fx = Path(self.tmp) / "fx.json"
        self.fx.write_text(json.dumps({"tasks": {"report": {"writes": {
            "results/P1_report.md": "# round 3\n", "results/P1_choices.json": json.dumps(choices)}}},
            "reviews": {"report": [[]]}}))
        self.common = ["--target", str(self.target), "--stage", "stage4_results", "--variable", "P1"]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_kill_review_after_two_recycles(self):
        store = Store(self.target)
        for i in (1, 2):
            store.append_jsonl("decision_log.jsonl", {"id": f"D00{i}", "variable": "P1", "gate_item_id": "CALL", "choice": "recycle"})
        self.assertEqual(main(["run", *self.common, "--mode", "fixtures", "--fixture", str(self.fx)]), 0)
        st = json.loads((self.target / ".rlo" / "state_stage4_results_P1.json").read_text())
        text = (self.target / st["gate_file"]).read_text()
        self.assertIn("## KILL-REVIEW-gate4:", text)
        self.assertIn("## CALL:", text)
        self.assertIn("## CHANGE-1-EITHER-WAY:", text)
        self.assertIn("AI default: report as not supported", text)
        self.assertEqual(text.count("Gate 4:"), 1)

    def test_no_kill_review_before_two_recycles(self):
        main(["run", *self.common, "--mode", "fixtures", "--fixture", str(self.fx)])
        st = json.loads((self.target / ".rlo" / "state_stage4_results_P1.json").read_text())
        self.assertNotIn("KILL-REVIEW", (self.target / st["gate_file"]).read_text())


if __name__ == "__main__":
    unittest.main()
