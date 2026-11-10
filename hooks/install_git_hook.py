#!/usr/bin/env python3
"""Install, remove or report the Neral git `pre-commit` stub.

Usage: install_git_hook.py install|uninstall|status [--repo DIR]
The stub runs hooks/git_pre_commit.py from this plugin. It fails open (exit 0) when that
script is gone, since the plugin path can change on update. A pre-commit hook without the
marker line is never overwritten or removed."""
import argparse, os, subprocess, sys  # noqa: E401
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

def hooks_dir(repo):
    def rev_parse(cwd, *args):
        r = subprocess.run(["git", "rev-parse", *args], cwd=cwd, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            sys.exit(f"neral: not a git repository: {repo}")
        return r.stdout.strip()
    top = rev_parse(repo, "--show-toplevel")
    return Path(top, rev_parse(top, "--git-path", "hooks"))

def is_ours(hook):
    try:
        return MARKER in hook.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False

def install(hook):
    existed = hook.exists()
    if existed and not is_ours(hook):
        print(f"neral: {hook} already exists and is not the Neral hook; nothing changed.")
        print(f'To chain it manually, add this line to that hook: python3 "{SCRIPT}" || exit 1')
        return 2
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(stub_text(SCRIPT), encoding="utf-8")
    hook.chmod(0o755)
    print(f"neral: git hook {'updated' if existed else 'installed'} at {hook}")
    return 0

def uninstall(hook):
    if not hook.exists():
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
    args = parser.parse_args(argv)
    hooks = hooks_dir(args.repo)
    hook = hooks / "pre-commit"
    if args.action == "install":
        return install(hook)
    if args.action == "uninstall":
        return uninstall(hook)
    print(f"{'installed' if is_ours(hook) else 'not installed'} (hooks dir: {hooks})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
