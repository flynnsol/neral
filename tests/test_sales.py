import unittest
from pathlib import Path

from test_product_manager import split_agent

ROOT = Path(__file__).resolve().parent.parent
SALES = ROOT / "agents" / "sales.md"
EXPECTED_TOOLS = ["Read", "Grep", "Glob", "WebSearch", "WebFetch"]
NEVER = (
    "never edit, create or delete files",
    "never read or write any notes vault",
    "never contact anyone",
    "never invent customers, quotes or numbers",
)


class SalesContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fm, cls.body = split_agent(SALES.read_text(encoding="utf-8"))
        cls.body_lower = cls.body.lower()
        cls.tools = [t.strip() for t in cls.fm.get("tools", "").split(",") if t.strip()]

    def test_name(self):
        self.assertEqual(self.fm.get("name"), "sales")

    def test_description(self):
        self.assertTrue(self.fm.get("description"))

    def test_model_opus(self):
        self.assertEqual(self.fm.get("model"), "opus")

    def test_tools_exact(self):
        self.assertEqual(self.tools, EXPECTED_TOOLS)

    def test_returns_audience_brief(self):
        self.assertIn("audience brief", self.body_lower)
        self.assertIn("docs/campaign-schema.md", self.body)

    def test_names_segments_marketing_targets(self):
        self.assertIn("`target_first`", self.body)
        self.assertIn("marketing targets first", self.body_lower)

    def test_never_rules(self):
        for rule in NEVER:
            with self.subTest(rule=rule):
                self.assertIn(rule, self.body_lower)

    def test_cites_sources(self):
        self.assertIn("cite a source", self.body_lower)


if __name__ == "__main__":
    unittest.main()
