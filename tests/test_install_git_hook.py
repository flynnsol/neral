import os, shutil, subprocess, sys, tempfile, unittest  # noqa: E401
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTALLER = ROOT / "hooks" / "install_git_hook.py"

def git(cwd, *args, env=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=env)

class InstallGitHookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name, "repo")
        self.repo.mkdir()
        self.env = {k: v for k, v in os.environ.items() if k != "NERAL_REVIEW" and not k.startswith("GIT_")}
        for args in (["init", "-q"], ["config", "user.name", "Test"], ["config", "user.email", "t@example.com"],
                     ["config", "core.hooksPath", ".git/hooks"], ["config", "commit.gpgsign", "false"]):
            git(self.repo, *args, env=self.env)
        self.hook = self.repo / ".git" / "hooks" / "pre-commit"
        (self.repo / "a.txt").write_text("hello\n")

    def tearDown(self):
        self.tmp.cleanup()

    def run_installer(self, *args, installer=INSTALLER):
        return subprocess.run([sys.executable, str(installer), *args, "--repo", str(self.repo)],
                              capture_output=True, text=True, env=self.env)

    def test_install_creates_executable_stub(self):
        r = self.run_installer("install")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.hook.read_text()
        self.assertTrue(text.startswith("#!/bin/sh\n"))
        self.assertIn("# neral-git-hook", text)
        self.assertIn(str((ROOT / "hooks" / "git_pre_commit.py").resolve()), text)
        self.assertTrue(os.access(self.hook, os.X_OK))
        self.assertIn("installed", self.run_installer("status").stdout)
        self.assertNotIn("not installed", self.run_installer("status").stdout)

    def test_commit_without_stamp_blocked_through_stub(self):
        self.run_installer("install")
        git(self.repo, "add", "a.txt", env=self.env)
        r = git(self.repo, "commit", "-m", "x", env=self.env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("neral:review", r.stderr)

    def test_install_twice_is_idempotent(self):
        self.run_installer("install")
        first = self.hook.read_text()
        r = self.run_installer("install")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("updated", r.stdout)
        self.assertEqual(self.hook.read_text(), first)

    def test_foreign_hook_refused_and_unchanged(self):
        self.hook.parent.mkdir(parents=True, exist_ok=True)
        self.hook.write_text("#!/bin/sh\necho mine\n")
        r = self.run_installer("install")
        self.assertEqual(r.returncode, 2)
        self.assertIn("git_pre_commit.py", r.stdout + r.stderr)
        self.assertEqual(self.hook.read_text(), "#!/bin/sh\necho mine\n")
        r = self.run_installer("uninstall")
        self.assertEqual(r.returncode, 0)
        self.assertTrue(self.hook.exists())
        self.assertIn("not installed", self.run_installer("status").stdout)

    def test_uninstall_removes_stub(self):
        self.run_installer("install")
        r = self.run_installer("uninstall")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.hook.exists())
        self.assertIn("not installed", self.run_installer("status").stdout)

    def test_missing_script_exits_zero(self):
        plugin = Path(self.tmp.name, "plugin", "hooks")
        plugin.mkdir(parents=True)
        shutil.copy(INSTALLER, plugin / "install_git_hook.py")
        (plugin / "git_pre_commit.py").write_text("import sys\nsys.exit(1)\n")
        self.run_installer("install", installer=plugin / "install_git_hook.py")
        self.assertNotEqual(subprocess.run([str(self.hook)], cwd=self.repo, env=self.env).returncode, 0)
        (plugin / "git_pre_commit.py").unlink()
        r = subprocess.run([str(self.hook)], cwd=self.repo, capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("neral", r.stderr)

    def test_honours_core_hooks_path(self):
        git(self.repo, "config", "core.hooksPath", "myhooks", env=self.env)
        r = self.run_installer("install")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("# neral-git-hook", (self.repo / "myhooks" / "pre-commit").read_text())
        self.assertFalse(self.hook.exists())

if __name__ == "__main__":
    unittest.main()
