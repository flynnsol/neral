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

    def test_wrapped_git_commit_is_detected(self):  # H1
        for cmd in ["(git commit -m x)", "{ git commit -m x; }", "if true; then git commit -m x; fi",
                    'bash -c "git commit -m x"', "env git commit", "command git commit",
                    "sudo git commit", "time git commit", "exec git commit", "nohup git commit",
                    "sh -c 'cd x && git commit'", "if a; then :; else git commit; fi",
                    "for f in x; do git commit; done", "env -u X FOO=1 git commit", "sudo -u me git commit",
                    'git commit -m "a\n\nb"', "cat <<EOF\nhi\nEOF\ngit commit"]:
            with self.subTest(cmd=cmd):
                self.assertTrue(gate.parse_command(cmd), cmd)

    def test_mentions_are_not_commands(self):  # H7
        for cmd in ["cat <<'EOF' > f.sh\ngit commit -m x\nEOF", "cat <<-EOF\n\tgit commit\n\tEOF",
                    'echo "git commit"', "python3 -c 'import os\ngit commit'",
                    'echo "notes\ngit commit -m y"', "printf '%s' 'a; git commit'", "# git commit"]:
            with self.subTest(cmd=cmd):
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

    def test_block_on_only_p0_to_p2(self):  # H5
        for value, want in [("P0", "P0"), ("P2", "P2"), ("P3", "P1"), ("P9", "P1"), ("p0", "P1")]:
            with self.subTest(value=value):
                self.assertEqual(gate.read_config(f"precommit:\n  block_on: {value}\n"), (True, want))

    def test_malformed_stamps_are_denied(self):  # H4
        bad = [json.dumps({"diff_sha256": DIGEST}),
               json.dumps({"diff_sha256": DIGEST, "verdict": "PASS"}),
               json.dumps({"diff_sha256": DIGEST, "worst_severity": None}),
               stamp(verdict="LGTM"), stamp(verdict=None), stamp(worst_severity="P4"),
               stamp(worst_severity=""), stamp(diff_sha256="A" * 64), stamp(diff_sha256="a" * 63),
               stamp(diff_sha256=None), stamp(diff_sha256="g" * 64), "[]"]
        for text in bad:
            with self.subTest(text=text):
                self.assertEqual(gate.check_stamp(text, DIGEST, "P1"), gate.REVIEW_MSG)
                self.assertEqual(gate.check_stamp(text, "A" * 64, "P1"), gate.REVIEW_MSG)

def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)

def opt_in(repo, text="profile: default\n"):
    (Path(repo) / ".neral").mkdir(exist_ok=True)
    (Path(repo) / ".neral/config.yml").write_text(text)

def install_stub(repo):
    (Path(repo) / ".git/hooks").mkdir(parents=True, exist_ok=True)
    (Path(repo) / ".git/hooks/pre-commit").write_text("#!/bin/sh\n# neral-git-hook\nexit 0\n")

class OptInTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q")
        (self.repo / "a.txt").write_text("hello\n")
        git(self.repo, "add", "a.txt")
        self.payload = {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}, "cwd": str(self.repo)}

    def tearDown(self):
        self.tmp.cleanup()

    def test_not_opted_in_allows(self):
        self.assertFalse(gate.repo_opted_in(str(self.repo)))
        self.assertIsNone(gate.decide(self.payload, {}))
        (self.repo / ".git/hooks").mkdir(exist_ok=True)
        (self.repo / ".git/hooks/pre-commit").write_text("#!/bin/sh\n# some other hook\n")
        self.assertIsNone(gate.decide(self.payload, {}))

    def test_config_opts_in(self):
        opt_in(self.repo)
        self.assertTrue(gate.repo_opted_in(str(self.repo)))
        self.assertIn("Run neral:review", gate.decide(self.payload, {}))

    def test_stub_opts_in(self):
        install_stub(self.repo)
        self.assertTrue(gate.repo_opted_in(str(self.repo)))
        self.assertIn("Run neral:review", gate.decide(self.payload, {}))

    def explicit_target(self):
        other = Path(self.tmp.name, "b")  # unrelated cwd repo B; self.repo/"a" is the target A
        target = self.repo / "a"
        for d in (other, target):
            d.mkdir()
            git(d, "init", "-q")
        (target / "f.txt").write_text("f\n")
        git(target, "add", "f.txt")
        return target, dict(self.payload, cwd=str(other))

    def test_explicit_target_with_stub_is_denied(self):  # F-1 (a), (b)
        target, payload = self.explicit_target()
        install_stub(target)
        for cmd in [f"git --git-dir={target}/.git commit -m x",
                    f"git --git-dir={target}/.git --work-tree={target} commit -m x"]:
            with self.subTest(cmd=cmd):
                p = dict(payload, tool_input={"command": cmd})
                self.assertIn("Run neral:review", gate.decide(p, {}))

    def test_dash_c_target_with_config_is_denied(self):  # F-1 (c)
        target, payload = self.explicit_target()
        opt_in(target)
        p = dict(payload, tool_input={"command": f"git -C {target} commit -m x"})
        self.assertIn("Run neral:review", gate.decide(p, {}))

    def test_explicit_target_with_foreign_hook_is_allowed(self):  # F-1 (d)
        target, payload = self.explicit_target()
        (target / ".git/hooks").mkdir(exist_ok=True)
        (target / ".git/hooks/pre-commit").write_text("#!/bin/sh\n# some other hook\n")
        for cmd in [f"git --git-dir={target}/.git commit -m x", f"git -C {target} commit -m x"]:
            with self.subTest(cmd=cmd):
                self.assertIsNone(gate.decide(dict(payload, tool_input={"command": cmd}), {}))

    def test_unreadable_hook_counts_as_opted_in(self):  # F-2
        (self.repo / ".git/hooks").mkdir(exist_ok=True)
        (self.repo / ".git/hooks/pre-commit").mkdir()  # exists but cannot be read as a file
        self.assertTrue(gate.repo_opted_in(str(self.repo)))
        self.assertIn("Run neral:review", gate.decide(self.payload, {}))

    def test_disabled_config_wins_over_stub(self):
        install_stub(self.repo)
        opt_in(self.repo, "precommit:\n  enabled: false\n")
        self.assertIsNone(gate.decide(self.payload, {}))

class DecideRealRepoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q")
        (self.repo / "a.txt").write_text("hello\n")
        opt_in(self.repo)
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
        opt_in(self.repo, "precommit:\n  enabled: false\n")
        self.assertIsNone(gate.decide(self.payload(), self.env))

    def test_git_dash_c_checks_target_repo(self):  # H3
        sub = self.repo / "sub"
        sub.mkdir()
        git(sub, "init", "-q")
        (sub / "b.txt").write_text("b\n")
        git(sub, "add", "b.txt")
        install_stub(sub)  # the target repo opts in through its own git hook
        self.assertIsNone(gate.decide(self.payload(), self.env))  # cwd repo has nothing staged
        for cmd in ["git -C sub commit -m x", "git --git-dir=sub/.git --work-tree sub commit"]:
            self.assertIn("Run neral:review", gate.decide(self.payload(cmd), self.env), cmd)
        for cmd in ["git -C missing commit", 'git -C "$DIR" commit']:
            self.assertIn("repo directory", gate.decide(self.payload(cmd), self.env), cmd)
        out = subprocess.run(["git", "diff", "--cached"], cwd=sub, capture_output=True).stdout
        (sub / ".git/neral").mkdir()
        (sub / ".git/neral/review-stamp.json").write_text(stamp(diff_sha256=hashlib.sha256(out).hexdigest()))
        self.assertIsNone(gate.decide(self.payload("git -C sub commit -m x"), self.env))

    def test_staged_digest_ignores_textconv_and_color(self):
        git(self.repo, "add", "a.txt")
        plain = subprocess.run(["git", "diff", "--cached"], cwd=self.repo, capture_output=True).stdout
        self.assertEqual(gate.staged_digest(self.repo), hashlib.sha256(plain).hexdigest())
        (self.repo / ".git/info").mkdir(exist_ok=True)
        (self.repo / ".git/info/attributes").write_text("*.txt diff=up\n")
        git(self.repo, "config", "diff.up.textconv", "tr a-z A-Z")
        git(self.repo, "config", "color.ui", "always")
        git(self.repo, "config", "diff.external", "false")
        conv = subprocess.run(["git", "diff", "--cached", "--no-ext-diff"], cwd=self.repo, capture_output=True).stdout
        self.assertNotEqual(conv, plain)  # the config really changes plain `git diff` output
        self.assertEqual(gate.staged_digest(self.repo), hashlib.sha256(plain).hexdigest())
        self.assertEqual(gate.staged_digest(self.repo.parent, ("-C", str(self.repo))), hashlib.sha256(plain).hexdigest())

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
            opt_in(d)
            r =self.run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": "git commit"}, "cwd": d}))
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("Run neral:review", out["permissionDecisionReason"])

if __name__ == "__main__":
    unittest.main()
