import hashlib, json, os, subprocess, sys, tempfile, unittest  # noqa: E401
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "hooks" / "git_pre_commit.py"

def git(cwd, *args, env=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=env)

class GitPreCommitHookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.env = {k: v for k, v in os.environ.items() if k != "NERAL_REVIEW" and not k.startswith("GIT_")}
        for args in (["init", "-q"], ["config", "user.name", "Test"], ["config", "user.email", "t@example.com"],
                     ["config", "core.hooksPath", ".git/hooks"], ["config", "commit.gpgsign", "false"]):
            git(self.repo, *args, env=self.env)
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.parent.mkdir(exist_ok=True)
        hook.write_text(f'#!/bin/sh\nexec python3 "{SCRIPT}"\n')
        hook.chmod(0o755)
        (self.repo / "a.txt").write_text("hello\n")

    def tearDown(self):
        self.tmp.cleanup()

    def run_git(self, *args, env=None):
        return git(self.repo, *args, env=env or self.env)

    def write_stamp(self):
        diff = subprocess.run(["git", "diff", "--cached"], cwd=self.repo, capture_output=True, env=self.env).stdout
        (self.repo / ".git" / "neral").mkdir(exist_ok=True)
        stamp = {"diff_sha256": hashlib.sha256(diff).hexdigest(), "verdict": "PASS", "worst_severity": None}
        (self.repo / ".git" / "neral" / "review-stamp.json").write_text(json.dumps(stamp))

    def commit_base(self):
        self.run_git("add", "a.txt")
        self.assertEqual(self.run_git("commit", "-q", "-m", "base", env={**self.env, "NERAL_REVIEW": "off"}).returncode, 0)

    def test_no_stamp_blocks(self):
        self.run_git("add", "a.txt")
        r = self.run_git("commit", "-m", "x")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("neral:review", r.stderr)

    def test_matching_stamp_allows(self):
        self.run_git("add", "a.txt")
        self.write_stamp()
        r = self.run_git("commit", "-m", "x")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_commit_all_without_stamp_blocks(self):
        self.commit_base()
        (self.repo / "a.txt").write_text("changed\n")
        r = self.run_git("commit", "-a", "-m", "x")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("neral:review", r.stderr)

    def test_stale_stamp_blocks(self):
        self.run_git("add", "a.txt")
        self.write_stamp()
        (self.repo / "a.txt").write_text("changed\n")
        self.run_git("add", "a.txt")
        r = self.run_git("commit", "-m", "x")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("changed since", r.stderr)

    def test_env_off_allows(self):
        self.run_git("add", "a.txt")
        r = self.run_git("commit", "-m", "x", env={**self.env, "NERAL_REVIEW": "off"})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_config_disabled_allows(self):
        (self.repo / ".neral").mkdir()
        (self.repo / ".neral" / "config.yml").write_text("precommit:\n  enabled: false\n")
        self.run_git("add", "a.txt")
        r = self.run_git("commit", "-m", "x")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_nothing_staged_exits_zero(self):
        r = subprocess.run([sys.executable, str(SCRIPT)], cwd=self.repo, capture_output=True, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)

if __name__ == "__main__":
    unittest.main()
