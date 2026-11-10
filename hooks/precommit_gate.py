#!/usr/bin/env python3
"""Neral pre-commit gate (PreToolUse hook): deny `git commit` without a valid review stamp.
See docs/review-stamp.md. Any error fails open (the commit is allowed)."""
import hashlib, json, os, re, shlex, subprocess, sys  # noqa: E401
from pathlib import Path

REVIEW_MSG = "Run neral:review on the staged changes (staged mode) before committing."
SEVERITIES = ("P0", "P1", "P2", "P3")
FLAGS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}

def parse_command(command):
    """Return True when any segment of a shell command line is a `git commit` invocation."""
    for segment in re.split(r"&&|\|\||[;|\n&]", command or ""):
        try:
            tokens = shlex.split(segment)
        except ValueError:
            tokens = segment.split()
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
            tokens.pop(0)
        if not tokens or os.path.basename(tokens[0]) != "git":
            continue
        i = 1
        while i < len(tokens) and tokens[i].startswith("-"):
            i += 2 if tokens[i] in FLAGS_WITH_ARG else 1
        if i < len(tokens) and tokens[i] == "commit":
            return True
    return False

def read_config(text):
    """Scan the `precommit:` block for `enabled` and `block_on`. Returns (enabled, block_on)."""
    enabled, block_on, inside = True, "P1", False
    for line in (text or "").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[0].isspace():
            inside = line.split("#")[0].strip() == "precommit:"
            continue
        if inside:
            key, _, value = line.split("#")[0].strip().partition(":")
            value = value.strip().strip("'\"")
            if key == "enabled":
                enabled = value.lower() != "false"
            elif key == "block_on" and value in SEVERITIES:
                block_on = value
    return enabled, block_on

def check_stamp(stamp_text, digest, block_on):
    """Return a deny reason, or None when the stamp is valid for the staged diff."""
    try:
        stamp = json.loads(stamp_text) if stamp_text is not None else None
    except ValueError:
        stamp = None
    if not isinstance(stamp, dict) or "diff_sha256" not in stamp:
        return REVIEW_MSG
    if stamp.get("diff_sha256") != digest:
        return "The staged diff changed since it was reviewed. " + REVIEW_MSG
    worst, verdict = stamp.get("worst_severity"), stamp.get("verdict")
    blocking = worst is not None and (worst not in SEVERITIES
                                      or SEVERITIES.index(worst) <= SEVERITIES.index(block_on))
    if blocking or verdict == "CHANGES NEEDED":
        return (f"The review found blocking issues (worst severity {worst}, verdict {verdict}). "
                "Fix them, restage and re-review with neral:review before committing.")
    return None

def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, timeout=30)

def decide(payload, env):
    """Return a deny reason for this hook payload, or None to allow."""
    command = (payload.get("tool_input") or {}).get("command", "")
    if payload.get("tool_name") != "Bash" or env.get("NERAL_REVIEW") == "off" or not parse_command(command):
        return None
    cwd = payload.get("cwd") or os.getcwd()
    top = git(cwd, "rev-parse", "--show-toplevel").stdout.decode().strip()
    if any("/.claude/worktrees/" in p.replace(os.sep, "/") + "/" for p in (cwd, top)):
        return None
    config = Path(top or cwd, ".neral", "config.yml")
    enabled, block_on = read_config(config.read_text(encoding="utf-8") if config.is_file() else "")
    if not enabled or git(cwd, "diff", "--cached", "--quiet").returncode != 1:
        return None  # disabled, nothing staged (0), or a git error (fail open)
    diff = git(cwd, "diff", "--cached")
    git_dir = git(cwd, "rev-parse", "--git-dir").stdout.decode().strip()
    stamp_path = Path(cwd, git_dir, "neral", "review-stamp.json")
    stamp_text = stamp_path.read_text(encoding="utf-8") if stamp_path.is_file() else None
    return check_stamp(stamp_text, hashlib.sha256(diff.stdout).hexdigest(), block_on)

def main():
    try:
        reason = decide(json.loads(sys.stdin.read()), os.environ)
    except Exception:
        return 0
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
              "permissionDecision": "deny", "permissionDecisionReason": reason}}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
