import contextlib, hashlib, io, json, os, subprocess, sys, tempfile, unittest  # noqa: E401
from pathlib import Path
from unittest import mock

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

    def run_script(self, script=SCRIPT, *flags):
        return subprocess.run([sys.executable, *flags, str(script)], cwd=self.repo, capture_output=True, text=True,
                              env=self.env)

    def test_history_replay_allows(self):
        self.run_git("add", "a.txt")
        self.assertEqual(self.run_script().returncode, 1)
        for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"):
            with self.subTest(marker=name):
                marker = self.repo / ".git" / name
                marker.mkdir() if name.startswith("rebase") else marker.write_text("0" * 40 + "\n")
                r = self.run_script()
                self.assertEqual(r.returncode, 0, r.stderr)
                marker.rmdir() if name.startswith("rebase") else marker.unlink()

    def test_undecodable_stamp_blocks(self):
        self.run_git("add", "a.txt")
        (self.repo / ".git" / "neral").mkdir()
        (self.repo / ".git" / "neral" / "review-stamp.json").write_bytes(b"\xff\xfe\x00bad")
        r = self.run_script()
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("Run neral:review", r.stderr)

    def test_textconv_and_color_do_not_change_digest(self):
        self.run_git("add", "a.txt")
        self.write_stamp()
        (self.repo / ".git" / "info").mkdir(exist_ok=True)
        (self.repo / ".git" / "info" / "attributes").write_text("*.txt diff=up\n")
        for args in (["diff.up.textconv", "tr a-z A-Z"], ["color.ui", "always"], ["diff.external", "false"]):
            self.run_git("config", *args)
        r = self.run_git("commit", "-m", "x")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_works_through_symlink(self):
        self.run_git("add", "a.txt")
        with tempfile.TemporaryDirectory() as d:
            link = Path(d, "pre-commit")
            link.symlink_to(SCRIPT)
            r = self.run_script(link, "-P")  # -P: Python itself does not add the script dir to sys.path
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("Run neral:review", r.stderr)

    def test_missing_gate_module_warns_and_allows(self):
        self.run_git("add", "a.txt")
        with tempfile.TemporaryDirectory() as d:
            lone = Path(d, "git_pre_commit.py")
            lone.write_text(SCRIPT.read_text())
            r = self.run_script(lone)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("neral", r.stderr.lower())
        self.assertEqual(len(r.stderr.strip().splitlines()), 1, r.stderr)

    def test_timeout_warns_and_allows(self):
        sys.path.insert(0, str(SCRIPT.parent))
        import git_pre_commit as hook
        self.assertEqual(hook.TIMEOUT, 120)
        err = io.StringIO()
        with mock.patch.object(hook, "decide", side_effect=subprocess.TimeoutExpired("git", 120)), \
                contextlib.redirect_stderr(err):
            self.assertEqual(hook.main(), 0)
        self.assertIn("timed out", err.getvalue())

if __name__ == "__main__":
    unittest.main()
