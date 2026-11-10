import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS_JSON = ROOT / "hooks" / "hooks.json"


class HooksJsonTest(unittest.TestCase):
    def load(self):
        return json.loads(HOOKS_JSON.read_text(encoding="utf-8"))

    def bash_commands(self):
        entries = self.load()["hooks"]["PreToolUse"]
        return [
            hook["command"]
            for entry in entries
            if entry.get("matcher") == "Bash"
            for hook in entry["hooks"]
            if hook.get("type") == "command"
        ]

    def test_parses_as_json(self):
        self.assertIsInstance(self.load(), dict)

    def test_pretooluse_bash_entry_runs_gate(self):
        commands = self.bash_commands()
        self.assertTrue(commands, "no PreToolUse command hook with matcher Bash")
        self.assertTrue(any("precommit_gate.py" in c for c in commands))

    def test_referenced_script_exists(self):
        for command in self.bash_commands():
            for path in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}(/[^\s\"']+)", command):
                self.assertTrue((ROOT / path.lstrip("/")).is_file(), path)
        self.assertTrue(any("${CLAUDE_PLUGIN_ROOT}/hooks/precommit_gate.py" in c for c in self.bash_commands()))


if __name__ == "__main__":
    unittest.main()
