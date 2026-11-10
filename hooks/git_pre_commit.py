#!/usr/bin/env python3
"""Neral git `pre-commit` hook: block the commit unless the review stamp matches the staged diff.

It only verifies the stamp (see docs/review-stamp.md); it never runs a review. Git runs
pre-commit after building the final index, so `commit -a`, `commit <paths>`, chained
`git add && git commit`, wrappers and subshells are all covered without parsing shell text.
Any error fails open (the commit is allowed)."""
import hashlib, os, subprocess, sys  # noqa: E401
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from precommit_gate import check_stamp, read_config  # noqa: E402

def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, timeout=30)

def decide(env, cwd):
    """Return a block reason for the staged changes, or None to allow."""
    if env.get("NERAL_REVIEW") == "off":
        return None
    top = git(cwd, "rev-parse", "--show-toplevel").stdout.decode().strip() or cwd
    if "/.claude/worktrees/" in top.replace(os.sep, "/") + "/":
        return None
    config = Path(top, ".neral", "config.yml")
    enabled, block_on = read_config(config.read_text(encoding="utf-8") if config.is_file() else "")
    if not enabled or git(top, "diff", "--cached", "--quiet").returncode != 1:
        return None  # disabled, nothing staged (0), or a git error (fail open)
    digest = hashlib.sha256(git(top, "diff", "--cached").stdout).hexdigest()
    stamp_path = Path(top, git(top, "rev-parse", "--git-path", "neral/review-stamp.json").stdout.decode().strip())
    stamp_text = stamp_path.read_text(encoding="utf-8") if stamp_path.is_file() else None
    return check_stamp(stamp_text, digest, block_on)

def main():
    try:
        reason = decide(os.environ, os.getcwd())
    except Exception:
        return 0
    if reason:
        print(reason, file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
