import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERIFIER = ROOT / "agents" / "verifier.md"
TESTER = ROOT / "agents" / "tester.md"


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


def tool_list(fm):
    return [t.strip() for t in fm["tools"].split(",") if t.strip()]


class VerifierContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fm, cls.body = split_agent(VERIFIER.read_text(encoding="utf-8"))

    def test_name(self):
        self.assertEqual(self.fm.get("name"), "verifier")

    def test_model_sonnet(self):
        self.assertEqual(self.fm.get("model"), "sonnet")

    def test_tools_exact_and_read_only(self):
        tools = tool_list(self.fm)
        self.assertEqual(len(tools), len(set(tools)), "duplicate tools")
        self.assertEqual(set(tools), {"Read", "Grep", "Glob", "Bash"})
        for banned in ("Edit", "Write", "NotebookEdit"):
            self.assertNotIn(banned, tools)

    def test_verdicts_defined(self):
        for verdict in ("CONFIRMED", "REFUTED", "INCONCLUSIVE"):
            self.assertIn(verdict, self.body)


class TesterContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fm, cls.body = split_agent(TESTER.read_text(encoding="utf-8"))
        cls.body_lower = cls.body.lower()

    def test_name(self):
        self.assertEqual(self.fm.get("name"), "tester")

    def test_model_sonnet(self):
        self.assertEqual(self.fm.get("model"), "sonnet")

    def test_tools_include_edit_write(self):
        tools = tool_list(self.fm)
        self.assertIn("Edit", tools)
        self.assertIn("Write", tools)

    def test_edits_restricted_to_test_paths(self):
        self.assertIn("test", self.body_lower)
        self.assertIn("tests/", self.body_lower)

    def test_forbids_source_changes(self):
        self.assertIn("source", self.body_lower)

    def test_reports_command_run(self):
        self.assertIn("command run", self.body_lower)


if __name__ == "__main__":
    unittest.main()
