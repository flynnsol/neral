import unittest
from pathlib import Path

from test_challenge_skill import split_skill

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "campaign" / "SKILL.md"

SKILL_PHRASES = {
    "gather": "gather the product",
    "schema": "docs/campaign-schema.md",
    "adjust_segments": "let the user adjust `target_first`",
    "pass_brief": "run `marketing` with the audience brief",
    "show_draft": "show the campaign draft and its copy",
    "explicit_yes": "only on the user's explicit yes",
    "never_without_yes": "never file, publish or send anything without a yes",
    "engram_plan": "file it with `engram:plan`",
    "map_done_when": "`done_when` becomes its acceptance",
    "map_owner": "`owner` its role",
    "map_deliverable": "`deliverable` goes into its body",
    "no_touches": "no `touches`",
    "fallback": "if engram is not installed, save the draft as a markdown file at a path the user names",
}


class CampaignSkillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fm, cls.body = split_skill(SKILL.read_text(encoding="utf-8"))
        cls.body_lower = " ".join(cls.body.lower().split())

    def test_name(self):
        self.assertEqual(self.fm.get("name"), "campaign")

    def test_description(self):
        desc = self.fm.get("description", "").lower()
        for word in ("campaign", "marketing", "sales", "pitch", "copy"):
            with self.subTest(word=word):
                self.assertIn(word, desc)

    def test_phrases(self):
        for key, phrase in SKILL_PHRASES.items():
            with self.subTest(key=key):
                self.assertIn(phrase, self.body_lower)

    def test_sales_before_marketing(self):
        sales = self.body_lower.find("run `sales`")
        marketing = self.body_lower.find("run `marketing`")
        self.assertNotEqual(sales, -1)
        self.assertNotEqual(marketing, -1)
        self.assertLess(sales, marketing)

    def test_yes_before_filing(self):
        yes = self.body_lower.find("only on the user's explicit yes")
        plan = self.body_lower.find("file it with `engram:plan`")
        self.assertNotEqual(yes, -1)
        self.assertLess(yes, plan)


if __name__ == "__main__":
    unittest.main()
