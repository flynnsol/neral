import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHITECT = ROOT / "agents" / "architect.md"
EXPECTED_TOOLS = {"Read", "Grep", "Glob", "Bash"}
FORBIDDEN_TOOLS = {"Edit", "Write", "NotebookEdit"}


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


class ArchitectContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fm, cls.body = split_agent(ARCHITECT.read_text(encoding="utf-8"))
        cls.body_lower = cls.body.lower()
        cls.tools = [t.strip() for t in cls.fm["tools"].split(",") if t.strip()]

    def test_name(self):
        self.assertEqual(self.fm.get("name"), "architect")

    def test_description(self):
        self.assertTrue(self.fm.get("description"))

    def test_model_opus(self):
        self.assertEqual(self.fm.get("model"), "opus")

    def test_no_write_tools(self):
        self.assertFalse(FORBIDDEN_TOOLS & set(self.tools))

    def test_tools_exact(self):
        self.assertEqual(len(self.tools), len(set(self.tools)), "duplicate tools")
        self.assertEqual(set(self.tools), EXPECTED_TOOLS)

    def test_names_three_areas(self):
        for area in ("high-level model:", "database:", "view architecture:"):
            with self.subTest(area=area):
                self.assertIn(area, self.body_lower)

    def test_references_pushback_schema(self):
        self.assertIn("docs/pushback-schema.md", self.body)

    def test_never_edits_files(self):
        self.assertIn("never edit", self.body_lower)

    def test_never_touches_vault(self):
        self.assertIn("never read or write any notes vault", self.body_lower)

    def test_challenges_only_when_warranted(self):
        self.assertIn("challenge only when", self.body_lower)
        self.assertIn("no evidence, no challenge", self.body_lower)

    def test_may_return_no_concerns(self):
        self.assertIn("no_concerns", self.body)

    def test_never_rewrites_plan(self):
        self.assertIn("never rewrite the plan", self.body_lower)

    def test_bash_read_only(self):
        self.assertIn("read-only", self.body_lower)
        self.assertIn("bash", self.body_lower)


if __name__ == "__main__":
    unittest.main()
