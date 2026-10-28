import random
import unittest

from rlo.calls import CallLog
from rlo.models.base import Finding, FindingResponse
from rlo.models.fixtures import FixtureAuthor, FixtureJudge
from rlo.resolve import resolve, route_for
import tempfile
from pathlib import Path


def f(id_, kind, checkable):
    return Finding(id=id_, severity="medium", kind=kind, claim="c", evidence="e", proposed_fix="p", checkable_by=checkable)


class Routing(unittest.TestCase):
    def test_routes(self):
        self.assertEqual(route_for(f("a", "error", "test")), "test")
        self.assertEqual(route_for(f("b", "error", "rule")), "test")
        self.assertEqual(route_for(f("c", "judgment", "none")), "human")
        self.assertEqual(route_for(f("d", "error", "none")), "judge")

    def test_blinding_is_unblinded_correctly(self):
        # Judge always picks "A". Over many seeds, the unblinded outcome must match whether A was the author.
        with tempfile.TemporaryDirectory() as d:
            calls = CallLog(Path(d) / "calls")
            author = FixtureAuthor({}, Path(d), calls)
            judge = FixtureJudge({"judge": {"d": "A"}}, calls)
            ctx = {"stage": "s", "variable": "v"}
            outcomes = set()
            for seed in range(20):
                rep = resolve([(f("d", "error", "none"), FindingResponse(id="d", verdict="reject", reason="r"))],
                              author, judge, ctx, rng=random.Random(seed))
                r = rep.resolutions[0]
                outcomes.add(r.outcome)
                # whichever position was A is the one the judge picked; sided_with must agree with outcome
                self.assertEqual(r.verdict.sided_with, r.outcome)
                self.assertEqual(calls.all()[-1].request["A"] == "r", r.outcome == "author")
            self.assertEqual(outcomes, {"author", "reviewer"})

    def test_test_route_decides_without_judge(self):
        with tempfile.TemporaryDirectory() as d:
            calls = CallLog(Path(d) / "calls")
            author = FixtureAuthor({"tests": {"t": {"author_position_held": False, "output": "fails"}}}, Path(d), calls)
            judge = FixtureJudge({}, calls)
            rep = resolve([(f("t", "error", "test"), FindingResponse(id="t", verdict="reject", reason="r"))],
                          author, judge, {"stage": "s", "variable": "v"})
            self.assertEqual(rep.resolutions[0].route, "test")
            self.assertEqual(rep.resolutions[0].outcome, "reviewer")
            self.assertTrue((Path(d) / "tests" / "dispute_t.txt").exists())
            self.assertEqual([c.role for c in calls.all()], ["test"])


if __name__ == "__main__":
    unittest.main()
