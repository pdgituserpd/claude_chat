import unittest

from rlo.gate import GateItem, parse, render, unanswered


class GateRoundTrip(unittest.TestCase):
    def setUp(self):
        self.items = [
            GateItem(id="C1", item="Year basis", options=["grant year", "filing year"], default="filing year",
                     precedent="Arts & Veugelers 2015", reason="invention timing"),
            GateItem(id="DISPUTE-F3", item="Panel edge", options=["author", "reviewer", "other"], default="",
                     precedent="", reason="first year inflated", source="dispute",
                     positions={"author": "flag first two years", "reviewer": "drop first k years"}),
        ]
        self.meta = dict(gate_no=2, title="Measures", stage="stage2_measures", variable="x", when="2026-10-28T00:00:00+00:00")

    def test_render_then_parse_preserves_fields(self):
        text = render(self.items, **self.meta)
        back = parse(text)
        self.assertEqual([i.id for i in back], ["C1", "DISPUTE-F3"])
        self.assertEqual(back[0].options, ["grant year", "filing year"])
        self.assertEqual(back[0].default, "filing year")
        self.assertEqual(back[1].positions["reviewer"], "drop first k years")
        self.assertEqual(unanswered(back), ["C1", "DISPUTE-F3"])

    def test_filled_choices_are_read_back(self):
        text = render(self.items, **self.meta)
        text = text.replace("Choice: \nNote: \n\n## DISPUTE", "Choice: grant year\nNote: I prefer grant year here\n\n## DISPUTE", 1)
        text = text.replace("Choice: \nNote: ", "Choice: author\nNote: ")
        back = parse(text)
        self.assertEqual(unanswered(back), [])
        self.assertEqual(back[0].choice, "grant year")
        self.assertEqual(back[0].note, "I prefer grant year here")
        self.assertEqual(back[1].choice, "author")

    def test_prose_edits_do_not_break_parsing(self):
        text = render(self.items, **self.meta)
        text = "Some notes I typed at the top.\n\n" + text + "\n\nAnd a trailing remark.\n"
        self.assertEqual(len(parse(text)), 2)


if __name__ == "__main__":
    unittest.main()
