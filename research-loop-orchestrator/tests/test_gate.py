import unittest

from rlo.gate import NO_DEFAULT, GateItem, parse, render, unanswered

META = dict(gate_no=2, title="Measures", stage="stage2_measures", variable="x", when="2026-11-01T00:00:00+00:00")


class DefaultRule(unittest.TestCase):
    def test_default_shown_only_with_direct_precedent(self):
        direct = GateItem(id="C1", item="Year basis", options=["grant", "filing"], default="filing",
                          precedent="Arts & Veugelers 2015", precedent_type="direct", reason="r")
        closest = GateItem(id="C2", item="Classes", options=["first", "all"], default="all",
                           precedent="Benner 2002 (closest)", precedent_type="closest", reason="r")
        none = GateItem(id="C3", item="Sample size", options=["100", "300"], default="300", precedent_type="none")
        text = render([direct, closest, none], **META)
        self.assertIn("AI default: filing", text)
        self.assertEqual(text.count(NO_DEFAULT), 2)
        back = parse(text)
        self.assertEqual(back[0].shown_default(), "filing")
        self.assertEqual(back[1].shown_default(), "")
        self.assertEqual(back[2].shown_default(), "")
        self.assertEqual([b.precedent_type for b in back], ["direct", "closest", "none"])

    def test_outcomes(self):
        it = GateItem(id="C1", item="i", options=["a", "b"], default="a", precedent="p", precedent_type="direct")
        it.choice = "a"
        self.assertEqual(it.outcome(), "accepted_default")
        it.choice = "b"
        self.assertEqual(it.outcome(), "overruled_default")
        it2 = GateItem(id="C2", item="i", options=["a", "b"], default="a", precedent_type="closest", choice="a")
        self.assertEqual(it2.outcome(), "chose")

    def test_round_trip_and_fill(self):
        items = [GateItem(id="C1", item="Year basis", options=["grant", "filing"], default="filing", precedent="AV 2015",
                          precedent_type="direct", reason="timing"),
                 GateItem(id="DISPUTE-F3", item="Panel edge", options=["author", "reviewer", "other"], source="dispute",
                          reason="first year inflated", positions={"author": "flag two years", "reviewer": "drop k years"})]
        text = "notes on top\n\n" + render(items, **META) + "\ntrailing remark\n"
        back = parse(text)
        self.assertEqual(unanswered(back), ["C1", "DISPUTE-F3"])
        self.assertEqual(back[1].positions["reviewer"], "drop k years")
        text = text.replace("Choice: \nNote: \n\n## DISPUTE", "Choice: grant\nNote: prefer grant\n\n## DISPUTE", 1)
        text = text.replace("Choice: \nNote: ", "Choice: author\nNote: ")
        back = parse(text)
        self.assertEqual(unanswered(back), [])
        self.assertEqual(back[0].outcome(), "overruled_default")
        self.assertEqual(back[0].note, "prefer grant")

    def test_bad_precedent_type_rejected(self):
        with self.assertRaises(ValueError):
            GateItem.from_choice_dict({"id": "C1", "item": "i", "options": ["a"], "precedent_type": "strong"})


if __name__ == "__main__":
    unittest.main()
