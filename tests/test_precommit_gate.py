import hashlib, json, os, subprocess, sys, tempfile, unittest  # noqa: E401
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "hooks"))
import precommit_gate as gate  # noqa: E402

DIGEST = "a" * 64

def stamp(**kw):
    return json.dumps({"diff_sha256": DIGEST, "verdict": "PASS", "worst_severity": None, **kw})

class PureFunctionsTest(unittest.TestCase):
    def test_parse_command(self):
        for cmd in ["git commit -m x", "git -C /r commit", "git -c a=b commit --amend --no-edit",
                    "cd x && git commit -m y", "ls; git --no-pager commit", "FOO=1 git commit"]:
            self.assertTrue(gate.parse_command(cmd), cmd)
        for cmd in ["git status", "echo git commit", "git log --grep commit", "", "gitcommit"]:
            self.assertFalse(gate.parse_command(cmd), cmd)

    def test_read_config(self):
        self.assertEqual(gate.read_config(""), (True, "P1"))
        text = "profile: strict\nprecommit:\n  enabled: false\n  block_on: P2\nother: 1\n"
        self.assertEqual(gate.read_config(text), (False, "P2"))
        self.assertEqual(gate.read_config("x:\n  enabled: false\n"), (True, "P1"))

    def test_missing_passing_and_stale_stamps(self):
        self.assertIn("Run neral:review", gate.check_stamp(None, DIGEST, "P1"))
        self.assertIn("Run neral:review", gate.check_stamp("{bad", DIGEST, "P1"))
        self.assertIsNone(gate.check_stamp(stamp(), DIGEST, "P1"))
        self.assertIsNone(gate.check_stamp(stamp(worst_severity="P2"), DIGEST, "P1"))
        self.assertIn("changed since", gate.check_stamp(stamp(diff_sha256="b" * 64), DIGEST, "P1"))

    def test_blocking(self):
        reason = gate.check_stamp(stamp(worst_severity="P1", verdict="PASS WITH NOTES"), DIGEST, "P1")
        self.assertIn("P1", reason)
        self.assertIn("re-review", reason)
        self.assertIsNotNone(gate.check_stamp(stamp(verdict="CHANGES NEEDED"), DIGEST, "P1"))
        self.assertIsNone(gate.check_stamp(stamp(worst_severity="P1"), DIGEST, "P0"))

def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)

class DecideRealRepoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q")
        (self.repo / "a.txt").write_text("hello\n")
        self.env = {}

    def tearDown(self):
        self.tmp.cleanup()

    def payload(self, cmd="git commit -m x", cwd=None):
        return {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(cwd or self.repo)}

    def write_stamp(self, **kw):
        out = subprocess.run(["git", "diff", "--cached"], cwd=self.repo, capture_output=True).stdout
        (self.repo / ".git/neral").mkdir(exist_ok=True)
        kw.setdefault("diff_sha256", hashlib.sha256(out).hexdigest())
        (self.repo / ".git/neral/review-stamp.json").write_text(stamp(**kw))

    def test_flow(self):
        self.assertIsNone(gate.decide(self.payload(), self.env))  # nothing staged
        git(self.repo, "add", "a.txt")
        self.assertIn("Run neral:review", gate.decide(self.payload(), self.env))
        self.write_stamp()
        self.assertIsNone(gate.decide(self.payload(), self.env))
        (self.repo / "a.txt").write_text("changed\n")
        git(self.repo, "add", "a.txt")
        self.assertIn("changed since", gate.decide(self.payload(), self.env))
        self.write_stamp(verdict="CHANGES NEEDED", worst_severity="P0")
        self.assertIn("P0", gate.decide(self.payload(), self.env))

    def test_bypasses(self):
        git(self.repo, "add", "a.txt")
        self.assertIsNone(gate.decide(self.payload(), {"NERAL_REVIEW": "off"}))
        self.assertIsNone(gate.decide(self.payload("git status"), self.env))
        self.assertIsNone(gate.decide({"tool_name": "Edit"}, self.env))
        wt = self.repo / ".claude/worktrees/x"
        wt.mkdir(parents=True)
        self.assertIsNone(gate.decide(self.payload(cwd=wt), self.env))
        (self.repo / ".neral").mkdir()
        (self.repo / ".neral/config.yml").write_text("precommit:\n  enabled: false\n")
        self.assertIsNone(gate.decide(self.payload(), self.env))

class MainTest(unittest.TestCase):
    def run_hook(self, stdin):
        return subprocess.run([sys.executable, str(ROOT / "hooks/precommit_gate.py")], input=stdin,
                              capture_output=True, text=True, env={**os.environ, "NERAL_REVIEW": ""})

    def test_malformed_input_allows(self):
        for stdin in ["not json", "[]", '{"tool_name":"Bash","tool_input":null}']:
            r = self.run_hook(stdin)
            self.assertEqual((r.returncode, r.stdout), (0, ""), stdin)

    def test_deny_output(self):
        with tempfile.TemporaryDirectory() as d:
            git(d, "init", "-q")
            Path(d, "f").write_text("x\n")
            git(d, "add", "f")
            r = self.run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": "git commit"}, "cwd": d}))
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("Run neral:review", out["permissionDecisionReason"])

if __name__ == "__main__":
    unittest.main()
