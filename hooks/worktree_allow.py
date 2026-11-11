#!/usr/bin/env python3
"""PreToolUse hook: auto-allow Edit and Write inside the repo's linked worktrees.

Allows only when every check succeeds; otherwise prints nothing so the normal
prompt runs. Never denies or asks. Acts only in repos that opted in to Neral
(same opt-in as the pre-commit gate). Rule: docs/integration-log.md (NER-50).
With NERAL_DEBUG=1 the fall-through reason goes to stderr; stdout is only ever the allow.
"""
import fnmatch
import json
import os
import subprocess
import sys
import time

CONTAINERS = (".claude/worktrees", ".worktrees")
EXCLUDED = (".claude", ".git*", ".mcp.json", ".github", ".husky", ".githooks", ".envrc", ".direnv",
            ".env*", ".vscode", ".idea", ".devcontainer", ".cargo", ".npmrc", ".yarnrc*", ".mise.toml",
            ".tool-versions", ".pre-commit-config.yaml", "claude*.md", "agents.md")
HOOK_MARKER = "# neral-git-hook"  # same marker as precommit_gate.HOOK_MARKER
# Unlike precommit_gate.py, this hook runs before every Edit and Write, so all git calls share one
# short deadline. GIT_* variables are scrubbed so an inherited GIT_DIR or GIT_WORK_TREE cannot make
# git describe a different repo than the one at cwd; this hook only ever trusts the filesystem.
DEADLINE_SECONDS = 4


class Skip(Exception):
    """Fall through to the normal prompt for the given reason."""


def git_lines(cwd, deadline, expect, *args):
    left = deadline - time.monotonic()
    if left <= 0:
        raise Skip("git deadline passed")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    proc = subprocess.run(["git", "rev-parse", "--path-format=absolute", *args], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=left)
    lines = proc.stdout.splitlines()
    return lines if proc.returncode == 0 and len(lines) == expect else None


def inside(path, root):
    return path.startswith(root.rstrip(os.sep) + os.sep)


def excluded(rel):
    return any(fnmatch.fnmatchcase(part.lower(), pat) for part in rel.split(os.sep) for pat in EXCLUDED)


def lexical_rel(path, root):
    """The remainder of `path` after its shortest lexical prefix whose realpath is `root`, or None."""
    parts = path.split(os.sep)
    for i in range(2, len(parts)):
        if os.path.realpath(os.sep.join(parts[:i]) or os.sep) == root:
            return os.sep.join(parts[i:])
    return None


def opted_in(main, hook):
    if os.path.isfile(os.path.join(main, ".neral", "config.yml")):
        return True
    try:
        with open(hook, encoding="utf-8", errors="replace") as f:
            return HOOK_MARKER in f.read().splitlines()
    except OSError:
        return False


def decide(payload, deadline):
    """Return an allow reason, or raise Skip."""
    if not isinstance(payload, dict):
        raise Skip("payload is not an object")
    tool = payload.get("tool_name")
    if not isinstance(tool, str) or tool not in ("Edit", "Write"):
        raise Skip("tool is not Edit or Write")
    cwd, tool_input = payload.get("cwd"), payload.get("tool_input")
    path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    if not (isinstance(cwd, str) and isinstance(path, str) and os.path.isabs(cwd) and os.path.isabs(path)):
        raise Skip("bad input")
    if not os.path.isdir(cwd):
        raise Skip("cwd is not a directory")
    found = git_lines(cwd, deadline, 2, "--git-common-dir", "--git-path", "hooks/pre-commit")
    if not found or not os.path.isabs(found[0]):
        raise Skip("no git common dir")
    common = os.path.realpath(found[0])
    if os.path.basename(common) != ".git":
        raise Skip("common dir is not named .git")
    main = os.path.dirname(common)
    hook = found[1] if os.path.isabs(found[1]) else os.path.join(cwd, found[1])
    if not opted_in(main, hook):
        raise Skip("not opted in")

    real = os.path.realpath(path)
    containers = [c for c in (os.path.realpath(os.path.join(main, c)) for c in CONTAINERS) if inside(c, main)]
    if not any(inside(real, c) for c in containers):
        raise Skip("not under a worktree container")
    probe = os.path.dirname(real)
    while not os.path.isdir(probe):
        probe = os.path.dirname(probe)
    found = git_lines(probe, deadline, 3, "--show-toplevel", "--git-dir", "--git-common-dir")
    if not found or not all(os.path.isabs(x) for x in found):
        raise Skip("no worktree toplevel")
    root, git_dir, wt_common = (os.path.realpath(x) for x in found)
    if git_dir == wt_common:
        raise Skip("not a linked worktree")
    if wt_common != common:
        raise Skip("worktree of another repo")
    if os.path.dirname(root) not in containers:
        raise Skip("not directly under a worktree container")
    if not inside(real, root):
        raise Skip("outside the worktree")
    lexical = lexical_rel(os.path.normpath(path), root)
    if excluded(os.path.relpath(real, root)) or (lexical is not None and excluded(lexical)):
        raise Skip("excluded path")
    if os.path.exists(real) and os.stat(real).st_nlink > 1:
        raise Skip("hardlink")
    return f"neral: {tool} inside linked worktree {root}"


def main():
    deadline = time.monotonic() + DEADLINE_SECONDS
    reason = None
    try:
        try:
            payload = json.loads(sys.stdin.read())
        except ValueError:
            raise Skip("malformed JSON")
        reason = decide(payload, deadline)
    except Skip as skip:
        why = str(skip)
    except Exception as exc:
        why = f"exception: {type(exc).__name__}: {exc}"
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": "allow",
                                                 "permissionDecisionReason": reason}}))
    elif os.environ.get("NERAL_DEBUG") == "1":
        sys.stderr.write(f"neral worktree_allow: fall through: {why}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
