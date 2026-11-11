import json, os, subprocess, sys, tempfile, unittest  # noqa: E401
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "hooks" / "worktree_allow.py"

def git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   cwd=cwd, check=True, capture_output=True)

def make_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q")
    (path / "a.txt").write_text("a\n")
    git(path, "add", "a.txt")
    git(path, "commit", "-q", "-m", "init")
    return path

def run(payload, debug=False):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    env = {k: v for k, v in os.environ.items() if k != "NERAL_DEBUG"}
    if debug:
        env["NERAL_DEBUG"] = "1"
    proc = subprocess.run([sys.executable, str(SCRIPT)], input=text, capture_output=True, text=True,
                          timeout=60, env=env)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout, proc.stderr

class WorktreeAllowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(os.path.realpath(self.tmp.name))
        self.main = make_repo(self.base / "main")
        git(self.main, "worktree", "add", "-q", ".worktrees/x", "-b", "x")
        git(self.main, "worktree", "add", "-q", ".claude/worktrees/y", "-b", "y")
        self.wt = self.main / ".worktrees/x"
        self.cwt = self.main / ".claude/worktrees/y"
        (self.main / ".neral").mkdir()
        (self.main / ".neral/config.yml").write_text("version: 1\n")

    def tearDown(self):
        self.tmp.cleanup()

    def payload(self, path, tool="Edit", cwd=None):
        return {"tool_name": tool, "cwd": str(cwd or self.main), "tool_input": {"file_path": str(path)}}

    def assert_allow(self, path, **kw):
        out, err = run(self.payload(path, **kw), debug=True)
        self.assertEqual(err, "", f"unexpected stderr for {path}")
        self.assertTrue(out, f"expected allow for {path}")
        hso = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "PreToolUse")
        self.assertEqual(hso["permissionDecision"], "allow")
        self.assertTrue(hso["permissionDecisionReason"])

    def assert_refused(self, payload, why):
        """Fall through for the expected reason, not because of a crash."""
        out, err = run(payload, debug=True)
        self.assertEqual(out, "", f"expected no stdout for {payload!r}")
        self.assertIn(f"fall through: {why}", err)
        self.assertNotIn("Traceback", err)
        self.assertNotIn("exception", err)
        quiet_out, quiet_err = run(payload)
        self.assertEqual((quiet_out, quiet_err), ("", ""))

    def assert_silent(self, path, why, **kw):
        self.assert_refused(self.payload(path, **kw), why)

    def test_allows_inside_worktrees(self):
        for wt in (self.wt, self.cwt):
            for cwd in (self.main, wt):
                for tool in ("Edit", "Write"):
                    with self.subTest(wt=wt, cwd=cwd, tool=tool):
                        self.assert_allow(wt / "a.txt", cwd=cwd, tool=tool)
                        self.assert_allow(wt / "new/dir/b.py", cwd=cwd, tool=tool)

    def test_in_worktree_symlink_to_plain_file_allowed(self):
        os.symlink(self.wt / "a.txt", self.wt / "link.txt")
        self.assert_allow(self.wt / "link.txt")

    def test_symlinked_ancestor_allowed(self):
        # Like /tmp -> /private/tmp: an ancestor of the repo is a symlink.
        os.symlink(self.base, self.base / "up")
        alias = self.base / "up/main"
        self.assert_allow(alias / ".worktrees/x/a.txt", cwd=alias)
        self.assert_allow(alias / ".claude/worktrees/y/new/b.txt", cwd=self.main)
        os.symlink(self.main, self.base / "alias")
        self.assert_allow(self.base / "alias/.worktrees/x/a.txt", cwd=self.wt)

    def test_symlinked_ancestor_still_applies_exclusions(self):
        os.symlink(self.main, self.base / "alias")
        wt = self.base / "alias/.worktrees/x"
        (self.wt / ".claude").mkdir()
        os.symlink(self.wt / ".claude", self.wt / "docs")
        self.assert_silent(wt / "docs/settings.json", "excluded path")
        self.assert_silent(wt / ".claude/settings.json", "excluded path")
        (self.wt / "vs").mkdir()
        os.symlink(self.wt / "vs", self.wt / ".vscode")
        self.assert_silent(wt / ".vscode/settings.json", "excluded path")
        self.assert_silent(self.wt / ".vscode/settings.json", "excluded path")

    def test_not_opted_in_falls_through(self):
        (self.main / ".neral/config.yml").unlink()
        self.assert_silent(self.wt / "a.txt", "not opted in")
        self.assert_silent(self.wt / "a.txt", "not opted in", cwd=self.wt)
        hook = self.main / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\necho other hook\n")
        self.assert_silent(self.wt / "a.txt", "not opted in")

    def test_opted_in_by_main_config_only(self):
        self.assertFalse((self.wt / ".neral").exists())
        self.assert_allow(self.wt / "a.txt", cwd=self.wt)
        self.assert_allow(self.cwt / "a.txt", cwd=self.cwt)

    def test_opted_in_by_git_hook_stub(self):
        (self.main / ".neral/config.yml").unlink()
        hook = self.main / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\n# neral-git-hook\nexec python3 x\n")
        self.assert_allow(self.wt / "a.txt")
        self.assert_allow(self.wt / "a.txt", cwd=self.wt)

    def test_escapes_fall_through(self):
        (self.main / ".worktrees-evil").mkdir()
        os.symlink(self.base, self.wt / "out")
        for path, why in [(f"{self.wt}/../../a.txt", "not under a worktree container"),
                          (f"{self.wt}/../x/../../a.txt", "not under a worktree container"),
                          (self.main / ".worktrees-evil/a.txt", "not under a worktree container"),
                          (self.wt / "out/main/a.txt", "not under a worktree container"),
                          (self.main / "a.txt", "not under a worktree container"),
                          (self.main / ".worktrees/a.txt", "not a linked worktree")]:
            with self.subTest(path=path):
                self.assert_silent(path, why)

    def test_nested_worktree_falls_through(self):
        git(self.main, "worktree", "add", "-q", ".worktrees/deep/w", "-b", "w")
        self.assert_silent(self.main / ".worktrees/deep/w/a.txt", "not directly under a worktree container")

    def test_standalone_clone_under_container_falls_through(self):
        git(self.base, "clone", "-q", str(self.main), str(self.main / ".worktrees/c"))
        self.assert_silent(self.main / ".worktrees/c/a.txt", "not a linked worktree")

    def test_separate_git_dir_falls_through(self):
        sep = self.base / "sep"
        sep.mkdir()
        git(sep, "init", "-q", f"--separate-git-dir={self.base / 'sep.gitdir'}")
        (sep / "a.txt").write_text("a\n")
        git(sep, "add", "a.txt")
        git(sep, "commit", "-q", "-m", "init")
        git(sep, "worktree", "add", "-q", ".worktrees/w", "-b", "w")
        (sep / ".neral").mkdir()
        (sep / ".neral/config.yml").write_text("version: 1\n")
        self.assert_silent(sep / ".worktrees/w/a.txt", "common dir is not named .git", cwd=sep)

    def test_symlinked_container_outside_falls_through(self):
        main2 = make_repo(self.base / "main2")
        (main2 / ".neral").mkdir()
        (main2 / ".neral/config.yml").write_text("version: 1\n")
        (self.base / "outside").mkdir()
        os.symlink(self.base / "outside", main2 / ".worktrees")
        git(main2, "worktree", "add", "-q", str(self.base / "outside/z"), "-b", "z")
        self.assert_silent(main2 / ".worktrees/z/a.txt", "not under a worktree container", cwd=main2)
        self.assert_silent(self.base / "outside/z/a.txt", "not under a worktree container", cwd=main2)

    def test_worktree_of_other_repo_falls_through(self):
        other = make_repo(self.base / "other")
        git(other, "worktree", "add", "-q", ".worktrees/q", "-b", "q")
        self.assert_silent(other / ".worktrees/q/a.txt", "not under a worktree container")
        self.assert_silent(other / ".worktrees/q/a.txt", "not under a worktree container", cwd=self.wt)
        git(other, "worktree", "add", "-q", str(self.main / ".worktrees/q2"), "-b", "q2")
        self.assert_silent(self.main / ".worktrees/q2/a.txt", "worktree of another repo")

    def test_exclusions_fall_through(self):
        names = [".claude/settings.json", ".git/config", ".gitmodules", ".gitattributes", ".GIT/hooks/x",
                 ".mcp.json", ".github/workflows/ci.yml", ".husky/pre-commit", ".githooks/x", ".envrc",
                 ".direnv/x", ".env", ".env.local", ".vscode/settings.json", ".idea/x.xml",
                 ".devcontainer/devcontainer.json", ".cargo/config.toml", ".npmrc", ".yarnrc.yml",
                 ".mise.toml", ".tool-versions", ".pre-commit-config.yaml", "CLAUDE.md", "claude.local.md",
                 "sub/CLAUDE.md", "AGENTS.md", "pkg/.Claude/x", "src/.ENVRC"]
        for name in names:
            with self.subTest(name=name):
                self.assert_silent(self.wt / name, "excluded path")

    def test_symlinks_into_exclusions_fall_through(self):
        (self.wt / ".claude").mkdir()
        (self.wt / ".envrc").write_text("x\n")
        os.symlink(self.wt / ".claude", self.wt / "docs")
        os.symlink(self.wt / ".envrc", self.wt / "notes.txt")
        self.assert_silent(self.wt / "docs/settings.json", "excluded path")
        self.assert_silent(self.wt / "notes.txt", "excluded path")

    def test_hardlink_falls_through(self):
        os.link(self.wt / "a.txt", self.wt / "h.txt")
        self.assert_silent(self.wt / "h.txt", "hardlink")

    def test_other_inputs_fall_through(self):
        self.assert_silent(self.wt / "a.txt", "tool is not Edit or Write", tool="Bash")
        self.assert_silent(self.wt / "a.txt", "tool is not Edit or Write", tool="NotebookEdit")
        self.assert_silent(self.wt / "a.txt", "tool is not Edit or Write", tool=["Edit"])
        self.assert_silent(self.wt / "a.txt", "tool is not Edit or Write", tool=5)
        self.assert_silent(self.wt / "a.txt", "no git common dir", cwd=self.base)
        self.assert_silent(self.wt / "a.txt", "cwd is not a directory", cwd=self.base / "missing/dir")
        self.assert_silent("a.txt", "bad input", cwd=self.wt)
        self.assert_silent("/neral-test-missing-root/sub/b.txt", "not under a worktree container")
        wt_file = str(self.wt / "a.txt")
        for bad, why in [("{not json", "malformed JSON"), ("", "malformed JSON"),
                         ("[]", "payload is not an object"),
                         ({"tool_name": "Edit", "cwd": str(self.main), "tool_input": {}}, "bad input"),
                         ({"tool_name": "Edit", "cwd": str(self.main), "tool_input": {"file_path": 5}}, "bad input"),
                         ({"tool_name": "Edit", "tool_input": {"file_path": wt_file}}, "bad input"),
                         ({"tool_name": "Edit", "cwd": "rel", "tool_input": {"file_path": wt_file}}, "bad input")]:
            with self.subTest(bad=bad):
                self.assert_refused(bad, why)

    def test_exception_is_reported_on_stderr_only(self):
        payload = self.payload(str(self.wt) + "/a\x00b.txt")
        out, err = run(payload, debug=True)
        self.assertEqual(out, "")
        self.assertIn("fall through: exception: ValueError", err)
        self.assertEqual(run(payload), ("", ""))


if __name__ == "__main__":
    unittest.main()
