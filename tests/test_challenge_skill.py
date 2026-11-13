import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "challenge" / "SKILL.md"
BRIEF = ROOT / "skills" / "challenge" / "brief.md"

SKILL_PHRASES = {
    "main_session": "run this skill in the main session",
    "parallel": "launch `architect` and `product-manager` in parallel",
    "schema": "docs/pushback-schema.md",
    "drop_no_evidence": "drop every challenge without `evidence`",
    "overlap_rule": "two challenges overlap when they cite the same plan ticket or section and concern the same decision or limit",
    "merge_keep": "keep the higher severity, name both agents",
    "merge_questions": "keep both questions only if they differ",
    "no_merge_different": "different concerns about the same ticket do not merge",
    "rank": "rank `blocker`, then `major`, then `minor`",
    "assumptions": "show every agent's `assumptions`",
    "relay": "relay the user's answers back",
    "ask_user": "askuserquestion",
    "no_concerns": "if both agents return `no_concerns`",
    "never_invent": "never invent challenges",
    "never_edit": "never edit or rewrite the plan",
    "no_vault": "never pass a vault path to the agents",
    "no_vault_read": "never let them read the vault",
    "plan_as_text": "pass the plan as text",
    "malformed": "if an agent returns malformed output",
    "show_raw": "show it raw and continue with the other agent's report",
}

BRIEF_FIELDS = {
    "plan_text": "plan text",
    "repo_path": "repo path",
    "project_rules": "project rules (optional)",
    "engineers_note": "engineers later get only tickets that pass",
}


def split_skill(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing leading '---'")
    fields = {}
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return fields, "\n".join(lines[i + 1:])
        if ":" in line and not line.startswith((" ", "\t", "#")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    raise ValueError("missing closing '---'")


class ChallengeSkillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fm, cls.body = split_skill(SKILL.read_text(encoding="utf-8"))
        cls.body_lower = " ".join(cls.body.lower().split())

    def test_name(self):
        self.assertEqual(self.fm.get("name"), "challenge")

    def test_description(self):
        desc = self.fm.get("description", "").lower()
        self.assertIn("challenge", desc)
        self.assertIn("before it is accepted", desc)

    def test_phrases(self):
        for key, phrase in SKILL_PHRASES.items():
            with self.subTest(key=key):
                self.assertIn(phrase, self.body_lower)

    def test_references_brief(self):
        self.assertIn("brief.md", self.body)


class ChallengeBriefTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = " ".join(BRIEF.read_text(encoding="utf-8").lower().split())

    def test_fields(self):
        for key, phrase in BRIEF_FIELDS.items():
            with self.subTest(key=key):
                self.assertIn(phrase, self.text)


if __name__ == "__main__":
    unittest.main()
