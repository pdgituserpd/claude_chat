import tempfile
import unittest
from pathlib import Path

from rlo.fingerprint import compare, fingerprint_outputs, load_snapshot, save_snapshot


class Fingerprints(unittest.TestCase):
    def test_identical_then_changed(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d)
            (t / "out").mkdir()
            (t / "out" / "a.csv").write_text("1,2\n")
            fp1 = fingerprint_outputs(t, ["out/**/*"])
            fp2 = fingerprint_outputs(t, ["out/**/*"])
            self.assertTrue(compare(fp1, fp2)["identical"])
            (t / "out" / "a.csv").write_text("1,3\n")
            (t / "out" / "b.csv").write_text("x\n")
            diff = compare(fp1, fingerprint_outputs(t, ["out/**/*"]))
            self.assertFalse(diff["identical"])
            self.assertEqual(diff["changed"], ["out/a.csv"])
            self.assertEqual(diff["added"], ["out/b.csv"])

    def test_snapshot_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "snap.json"
            self.assertIsNone(load_snapshot(p))
            save_snapshot(p, {"a": "1"}, {"m": 1})
            self.assertEqual(load_snapshot(p), {"a": "1"})


if __name__ == "__main__":
    unittest.main()
