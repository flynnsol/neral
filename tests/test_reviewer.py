import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEWER = ROOT / "agents" / "reviewer.md"
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


class ReviewerContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fm, cls.body = split_agent(REVIEWER.read_text(encoding="utf-8"))
        cls.body_lower = cls.body.lower()
        cls.tools = [t.strip() for t in cls.fm["tools"].split(",") if t.strip()]

    def test_name(self):
        self.assertEqual(self.fm.get("name"), "reviewer")

    def test_model_sonnet(self):
        self.assertEqual(self.fm.get("model"), "sonnet")

    def test_no_write_tools(self):
        self.assertFalse(FORBIDDEN_TOOLS & set(self.tools))

    def test_tools_exact(self):
        self.assertEqual(len(self.tools), len(set(self.tools)), "duplicate tools")
        self.assertEqual(set(self.tools), EXPECTED_TOOLS)

    def test_references_finding_schema(self):
        self.assertIn("docs/finding-schema.md", self.body)

    def test_bash_read_only(self):
        self.assertIn("read-only", self.body_lower)
        self.assertIn("bash", self.body_lower)


if __name__ == "__main__":
    unittest.main()
