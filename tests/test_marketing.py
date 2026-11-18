import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETING = ROOT / "agents" / "marketing.md"
EXPECTED_TOOLS = {"Read", "Grep", "Glob", "WebSearch", "WebFetch"}
FORBIDDEN_TOOLS = {"Edit", "Write", "NotebookEdit", "Bash"}
COPY_KINDS = ("headlines", "posts", "emails", "landing")


def split_agent(text):
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


class MarketingContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fm, cls.body = split_agent(MARKETING.read_text(encoding="utf-8"))
        cls.body_lower = cls.body.lower()
        cls.tools = [t.strip() for t in cls.fm["tools"].split(",") if t.strip()]

    def test_name(self):
        self.assertEqual(self.fm.get("name"), "marketing")

    def test_description(self):
        self.assertTrue(self.fm.get("description"))

    def test_model_opus(self):
        self.assertEqual(self.fm.get("model"), "opus")

    def test_color(self):
        self.assertTrue(self.fm.get("color"))

    def test_tools_exact(self):
        self.assertEqual(len(self.tools), len(set(self.tools)), "duplicate tools")
        self.assertEqual(set(self.tools), EXPECTED_TOOLS)

    def test_no_write_tools(self):
        self.assertFalse(FORBIDDEN_TOOLS & set(self.tools))

    def test_references_campaign_schema(self):
        self.assertIn("docs/campaign-schema.md", self.body)

    def test_returns_epic_with_tickets(self):
        self.assertIn("campaign draft", self.body_lower)
        self.assertIn("epic", self.body_lower)
        self.assertIn("tickets", self.body_lower)

    def test_copy_and_ideas(self):
        for kind in COPY_KINDS:
            with self.subTest(kind=kind):
                self.assertIn(kind, self.body_lower)
        self.assertIn("ideas", self.body_lower)

    def test_plain_language(self):
        self.assertIn("plain, non-technical language", self.body_lower)

    def test_follows_sales_segments(self):
        self.assertIn("`target_first`", self.body)
        self.assertIn("segments sales picked", self.body_lower)

    def test_never_edits_files(self):
        self.assertIn("never edit, create or delete files", self.body_lower)

    def test_never_touches_vault(self):
        self.assertIn("never read or write any notes vault", self.body_lower)

    def test_never_publishes(self):
        self.assertIn("never publish, post or send anything", self.body_lower)

    def test_no_unbacked_claims(self):
        self.assertIn("no claims the product cannot back", self.body_lower)


if __name__ == "__main__":
    unittest.main()
