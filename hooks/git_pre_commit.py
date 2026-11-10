#!/usr/bin/env python3
"""Neral git `pre-commit` hook: block the commit unless the review stamp matches the staged diff.

It only verifies the stamp (see docs/review-stamp.md); it never runs a review. Git runs
pre-commit after building the final index, so `commit -a`, `commit <paths>`, chained
`git add && git commit`, wrappers and subshells are all covered without parsing shell text.
Any error fails open (the commit is allowed). Merges, cherry-picks, reverts and rebases replay
history that was already committed, so they are not checked."""
import os, subprocess, sys  # noqa: E401
from pathlib import Path

TIMEOUT = 120
REPLAY_MARKERS = ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply")

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
try:
    from precommit_gate import check_stamp, read_config, staged_digest  # noqa: E402
except ImportError as exc:
    print(f"neral pre-commit: cannot load precommit_gate ({exc}); review stamp not checked.", file=sys.stderr)
    sys.exit(0)

def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, timeout=TIMEOUT)

def git_path(top, name):
    return Path(top, git(top, "rev-parse", "--git-path", name).stdout.decode().strip())

def read_stamp(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None  # missing, unreadable or undecodable: treated as no stamp

def decide(env, cwd):
    """Return a block reason for the staged changes, or None to allow."""
    if env.get("NERAL_REVIEW") == "off":
        return None
    top = git(cwd, "rev-parse", "--show-toplevel").stdout.decode().strip() or cwd
    if "/.claude/worktrees/" in top.replace(os.sep, "/") + "/":
        return None
    if any(git_path(top, name).exists() for name in REPLAY_MARKERS):
        return None
    config = Path(top, ".neral", "config.yml")
    enabled, block_on = read_config(config.read_text(encoding="utf-8") if config.is_file() else "")
    if not enabled or git(top, "diff", "--cached", "--quiet").returncode != 1:
        return None  # disabled, nothing staged (0), or a git error (fail open)
    digest = staged_digest(top, timeout=TIMEOUT)
    return check_stamp(read_stamp(git_path(top, "neral/review-stamp.json")), digest, block_on)

def main():
    try:
        reason = decide(os.environ, os.getcwd())
    except subprocess.TimeoutExpired:
        print(f"neral pre-commit: git timed out after {TIMEOUT}s; review stamp not checked.", file=sys.stderr)
        return 0
    except Exception:
        return 0
    if reason:
        print(reason, file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
