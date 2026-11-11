import json
import os
import re
import subprocess
import tempfile
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

    def test_edit_write_entry_runs_worktree_allow(self):
        entries = [e for e in self.load()["hooks"]["PreToolUse"] if e.get("matcher") == "Edit|Write"]
        self.assertEqual(len(entries), 1, "no single PreToolUse entry with matcher Edit|Write")
        commands = [h["command"] for h in entries[0]["hooks"] if h.get("type") == "command"]
        self.assertIn('python3 "${CLAUDE_PLUGIN_ROOT}/hooks/worktree_allow.py"', commands)
        self.assertTrue((ROOT / "hooks" / "worktree_allow.py").is_file())

    def test_edit_write_command_runs_through_shell(self):
        entry = next(e for e in self.load()["hooks"]["PreToolUse"] if e.get("matcher") == "Edit|Write")
        hook = next(h for h in entry["hooks"] if h.get("type") == "command")
        self.assertIsInstance(hook.get("timeout"), int)
        self.assertGreater(hook["timeout"], 0)
        command = hook["command"].replace("${CLAUDE_PLUGIN_ROOT}", str(ROOT))
        with tempfile.TemporaryDirectory() as tmp:
            main = Path(os.path.realpath(tmp)) / "main"
            main.mkdir()
            env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
            for args in (["init", "-q"], ["commit", "-q", "--allow-empty", "-m", "init"],
                         ["worktree", "add", "-q", ".worktrees/x", "-b", "x"]):
                subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
                               cwd=main, check=True, capture_output=True, env=env)
            (main / ".neral").mkdir()
            (main / ".neral/config.yml").write_text("version: 1\n")
            payload = {"tool_name": "Write", "cwd": str(main),
                       "tool_input": {"file_path": str(main / ".worktrees/x/new.txt")}}
            proc = subprocess.run(command, shell=True, input=json.dumps(payload), capture_output=True,
                                  text=True, timeout=hook["timeout"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual((out["hookEventName"], out["permissionDecision"]), ("PreToolUse", "allow"))


if __name__ == "__main__":
    unittest.main()
