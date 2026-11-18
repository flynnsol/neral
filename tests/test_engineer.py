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

    def lean_section(self):
        _, found, rest = self.body.partition("## Lean code")
        self.assertTrue(found, "missing '## Lean code' section")
        return rest.split("\n## ", 1)[0].lower()

    def test_lean_ladder_in_order(self):
        section = self.lean_section()
        steps = ["reuse", "standard library", "installed dependency", "minimum new code"]
        positions = [section.find(step) for step in steps]
        self.assertNotIn(-1, positions, f"ladder step missing: {steps}")
        self.assertEqual(positions, sorted(positions), "ladder out of order")

    def test_lean_no_speculative_code(self):
        section = self.lean_section()
        for phrase in ("abstraction", "option", "for later"):
            self.assertIn(phrase, section)

    def test_lean_deletion_beats_addition(self):
        self.assertIn("deletion beats addition", self.lean_section())

    def test_lean_never_cut(self):
        section = self.lean_section()
        for item in ("validation at trust boundaries", "data loss", "security", "accessibility"):
            self.assertIn(item, section)

    def test_method_points_at_lean_code(self):
        method = self.body.partition("## Method")[2].split("\n## ", 1)[0]
        self.assertIn("Lean code", method)


if __name__ == "__main__":
    unittest.main()
