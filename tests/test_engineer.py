import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINEER = ROOT / "agents" / "engineer.md"
EXPECTED_TOOLS = {"Read", "Grep", "Glob", "Edit", "Write", "Bash"}


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


class EngineerContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fm, cls.body = split_agent(ENGINEER.read_text(encoding="utf-8"))
        cls.body_lower = cls.body.lower()

    def test_tools_exact(self):
        tools = [t.strip() for t in self.fm["tools"].split(",") if t.strip()]
        self.assertEqual(len(tools), len(set(tools)), "duplicate tools")
        self.assertEqual(set(tools), EXPECTED_TOOLS)

    def test_model_opus(self):
        self.assertEqual(self.fm.get("model"), "opus")

    def test_touches_limit_rule(self):
        self.assertIn("touches", self.body_lower)

    def test_one_commit_rule(self):
        self.assertIn("one commit", self.body_lower)

    def test_no_vault_rule(self):
        self.assertIn("vault", self.body_lower)


if __name__ == "__main__":
    unittest.main()
