#!/usr/bin/env python3
"""Install, remove or report the Neral git `pre-commit` stub.

Usage: install_git_hook.py install|uninstall|status [--repo DIR] [--allow-shared-hooks-dir]
The stub runs hooks/git_pre_commit.py from this plugin. It fails open (exit 0) when that
script is gone, since the plugin path can change on update. A pre-commit hook without the
marker line, or a symlinked one, is never overwritten or removed. A hooks directory outside
the repository is only changed with --allow-shared-hooks-dir."""
import argparse, os, subprocess, sys, tempfile  # noqa: E401
from pathlib import Path

MARKER = "# neral-git-hook"
SCRIPT = Path(os.path.realpath(Path(__file__).resolve().parent / "git_pre_commit.py"))

def sh_quote(text):
    return "".join("\\" + c if c in '\\"$`' else c for c in text)

def stub_text(script):
    path = sh_quote(str(script))
    return (f'#!/bin/sh\n{MARKER}\n# Installed by /neral:config precommit install; checks the Neral review stamp.\n'
            f'script="{path}"\n'
            'if [ ! -f "$script" ]; then\n'
            '  echo "neral: git hook script not found at $script; commit allowed (re-run /neral:config precommit install)" >&2\n'
            '  exit 0\nfi\n'
            'exec python3 "$script" "$@"\n')

def fail(message):
    print(message, file=sys.stderr)
    sys.exit(2)

def hooks_dir(repo):
    """Return (hooks dir, is bare, dirs the hooks dir may live in without being shared)."""
    def rev_parse(cwd, *args):
        try:
            r = subprocess.run(["git", "rev-parse", *args], cwd=cwd, capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            fail(f"neral: not a git repository: {repo}")
        if r.returncode != 0:
            fail(f"neral: not a git repository: {repo}")
        return r.stdout.strip()
    bare = rev_parse(repo, "--is-bare-repository") == "true"
    base = repo if bare else rev_parse(repo, "--show-toplevel")
    roots = [Path(base, rev_parse(base, "--absolute-git-dir")), Path(base, rev_parse(base, "--git-common-dir"))]
    if not bare:
        roots.append(Path(base))
    return Path(base, rev_parse(base, "--git-path", "hooks")), bare, roots

def is_inside(path, roots):
    real = os.path.realpath(path)
    return any(os.path.commonpath([real, os.path.realpath(r)]) == os.path.realpath(r) for r in roots)

def refuse_symlink(hook):
    if os.path.islink(hook):
        print(f"neral: {hook} is a symlink; refusing to follow it. Nothing changed.", file=sys.stderr)
        return True
    return False

def is_ours(hook):
    if os.path.islink(hook):
        return False
    try:
        return MARKER in hook.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False

def write_atomic(hook, text):
    fd, tmp = tempfile.mkstemp(dir=hook.parent, prefix=".pre-commit.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.chmod(tmp, 0o755)
        os.replace(tmp, hook)
    except BaseException:
        if os.path.lexists(tmp):
            os.unlink(tmp)
        raise

def install(hook):
    if refuse_symlink(hook):
        return 2
    existed = os.path.lexists(hook)
    if existed and not is_ours(hook):
        print(f"neral: {hook} already exists and is not the Neral hook; nothing changed.")
        print(f'To chain it manually, add this line to that hook: python3 "{SCRIPT}" || exit 1')
        return 2
    hook.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(hook, stub_text(SCRIPT))
    print(f"neral: git hook {'updated' if existed else 'installed'} at {hook}")
    return 0

def uninstall(hook):
    if refuse_symlink(hook):
        return 2
    if not os.path.lexists(hook):
        print(f"neral: no pre-commit hook at {hook}; nothing to remove.")
    elif is_ours(hook):
        hook.unlink()
        print(f"neral: git hook removed from {hook}")
    else:
        print(f"neral: {hook} is not the Neral hook; left it in place.")
    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(description="Manage the Neral git pre-commit hook")
    parser.add_argument("action", choices=["install", "uninstall", "status"])
    parser.add_argument("--repo", default=os.getcwd())
    parser.add_argument("--allow-shared-hooks-dir", action="store_true",
                        help="allow a hooks directory outside the repository (for example a shared core.hooksPath)")
    args = parser.parse_args(argv)
    hooks, bare, roots = hooks_dir(args.repo)
    hook = hooks / "pre-commit"
    shared = not is_inside(hooks, roots)
    if args.action == "status":
        extra = ("; bare repository" if bare else "") + ("; outside the repository" if shared else "")
        print(f"{'installed' if is_ours(hook) else 'not installed'} (hooks dir: {hooks}{extra})")
        return 0
    if shared and not args.allow_shared_hooks_dir:
        print(f"neral: hooks directory {hooks} is outside this repository (shared core.hooksPath?); nothing changed. "
              "Re-run with --allow-shared-hooks-dir to change it anyway.", file=sys.stderr)
        return 2
    return install(hook) if args.action == "install" else uninstall(hook)

if __name__ == "__main__":
    sys.exit(main())
