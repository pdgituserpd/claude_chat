import tempfile
import unittest
from pathlib import Path

from rlo import logs
from rlo.state import Store


class ErrorLog(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def _entry(self, **over):
        kw = dict(type_="data", produced_by="not stated", how_found="row count jumped", found_by="coded check",
                  how_far="output", effect="duplicated firm-years", confirmed_by_rerun=True, fix="dedupe before merge",
                  check_added="unique key check", silent=True, wrong=True, in_research=True)
        kw.update(over)
        return logs.log_error(self.store, **kw)

    def test_three_tests_enforced(self):
        self.assertEqual(self._entry()["id"], "E001")
        for bad in ({"silent": False}, {"wrong": False}, {"in_research": False}):
            with self.assertRaises(ValueError):
                self._entry(**bad)
        with self.assertRaises(ValueError):
            self._entry(type_="style")
        with self.assertRaises(ValueError):
            self._entry(found_by="someone")
        self.assertEqual(self._entry()["id"], "E002")

    def test_stop_log_and_counts(self):
        with self.assertRaises(ValueError):
            logs.log_stop(self.store, paper="P9", call="dead", reason="r", decided_by="Pouya")
        logs.log_stop(self.store, paper="P9", call="shelved", reason="data blocked", decided_by="Pouya")
        self._entry()
        self._entry(in_development=True)
        logs.log_run(self.store, stage="s", variable="v", kind="k", git_commit="abc", inputs={}, outputs={}, settings={}, checks={})
        c = logs.counts(self.store)
        self.assertEqual(c["stopped_papers"], 1)
        self.assertEqual(c["silent_errors"], 2)
        self.assertEqual(c["silent_errors_in_audited_work"], 1)
        self.assertEqual(c["errors_per_run"], 1.0)

    def test_run_log_carries_software_versions(self):
        rec = logs.log_run(self.store, stage="s", variable="v", kind="k", git_commit="", inputs={}, outputs={}, settings={}, checks={})
        self.assertIn("python", rec["software_versions"])
        self.assertIn("rlo", rec["software_versions"])
        self.assertEqual(rec["git_commit"], "not stated")

    def test_judgment_log_counts_outcomes(self):
        from rlo.gate import GateItem

        items = [GateItem(id="C1", item="i", options=["a", "b"], default="a", precedent="p", precedent_type="direct", choice="a"),
                 GateItem(id="C2", item="i", options=["a", "b"], default="a", precedent="p", precedent_type="direct", choice="b"),
                 GateItem(id="C3", item="i", options=["a", "b"], precedent_type="none", choice="b")]
        ds = [logs.log_decision(self.store, it, stage="s", variable="v", decided_by="Pouya") for it in items]
        j = logs.log_judgment(self.store, gate=2, stage="s", variable="v", decisions=ds, decided_by="Pouya")
        self.assertEqual((j["accepted_default"], j["overruled_default"], j["chose"]), (1, 1, 1))
        self.assertEqual(j["overrule_rate"], 0.5)
        self.assertEqual(logs.counts(self.store)["default_overrule_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
