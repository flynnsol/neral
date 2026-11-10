#!/usr/bin/env python3
"""Neral pre-commit gate (PreToolUse hook): deny `git commit` without a valid review stamp.
Only enforced in repos that opted in (see repo_opted_in). See docs/review-stamp.md.
Any error fails open (the commit is allowed)."""
import hashlib, json, os, re, subprocess, sys, threading  # noqa: E401
from pathlib import Path

REVIEW_MSG = "Run neral:review on the staged changes (staged mode) before committing."
SEVERITIES = ("P0", "P1", "P2", "P3")
BLOCK_ON = ("P0", "P1", "P2")
VERDICTS = ("PASS", "PASS WITH NOTES", "CHANGES NEEDED")
SHA256 = re.compile(r"[0-9a-f]{64}")
TARGET_MSG = ("Could not tell which repository `git -C`/`--git-dir`/`--work-tree` points at. "
              "Run the commit from the repo directory instead.")
FLAGS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
KEYWORDS = {"{", "}", "!", "if", "then", "else", "elif", "do", "while", "until"}
WRAPPERS = {"env", "command", "sudo", "time", "exec", "nohup"}
WRAPPER_ARG = {"-u", "-g", "-C", "-D", "-h", "-p", "-U", "-r", "-t", "--user", "--group", "--chdir", "--unset"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
HEREDOC = re.compile(r"<<-?[ \t]*(['\"]?)([^\s'\";&|()<>]+)\1")
ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

def split_commands(text):
    """Split shell text into simple commands (word lists). Operators split only outside quotes;
    heredoc bodies and comments are skipped."""
    cmds, words, cur, heredocs, i, n = [], [], None, [], 0, len(text)
    while i < n:
        c = text[i]
        if c == "\\":
            if text[i + 1:i + 2] != "\n":
                cur = (cur or "") + text[i + 1:i + 2]
            i += 2
        elif c == "'":
            j = text.find("'", i + 1)
            j = n if j < 0 else j
            cur, i = (cur or "") + text[i + 1:j], j + 1
        elif c == '"':
            j, buf = i + 1, ""
            while j < n and text[j] != '"':
                j += text[j] == "\\" and text[j + 1:j + 2] in ('"', "\\", "$", "`")
                buf, j = buf + text[j:j + 1], j + 1
            cur, i = (cur or "") + buf, j + 1
        elif c == "#" and cur is None:
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif c == "<" and HEREDOC.match(text, i) and not text.startswith("<<<", i):
            m = HEREDOC.match(text, i)
            heredocs.append((m.group(2), m.group(0).startswith("<<-")))
            i = m.end()
        elif c in " \t\n;&|()":
            if cur is not None:
                words.append(cur)
            cur = None
            if c not in " \t" and words:
                cmds, words = cmds + [words], []
            if c == "\n":
                for delim, strip_tabs in heredocs:
                    while i < n:
                        j = text.find("\n", i + 1)
                        j = n if j < 0 else j
                        line, i = text[i + 1:j], j
                        if (line.lstrip("\t") if strip_tabs else line) == delim:
                            break
                heredocs = []
            i += 1
        else:
            cur, i = (cur or "") + c, i + 1
    words += [cur] if cur is not None else []
    return cmds + [words] if words else cmds

def commit_options(command, depth=0):
    """Return the git global options of the first `git commit` in a command line, else None.
    Looks through keywords, assignments, wrappers (env, sudo, ...) and `sh -c` strings."""
    for words in split_commands(command or ""):
        i = 0
        while i < len(words) and (words[i] in KEYWORDS or ASSIGN.match(words[i]) or words[i] in WRAPPERS):
            i += 1
            if words[i - 1] in WRAPPERS:
                while i < len(words) and words[i].startswith("-"):
                    i += 2 if words[i] in WRAPPER_ARG else 1
        words = words[i:]
        name = os.path.basename(words[0]) if words else ""
        j = 1
        while j < len(words) and words[j].startswith("-"):
            if name in SHELLS and not words[j].startswith("--") and "c" in words[j] and depth < 5:
                found = commit_options(" ".join(words[j + 1:j + 2]), depth + 1)
                if found is not None:
                    return found
                break
            j += 2 if name == "git" and words[j] in FLAGS_WITH_ARG else 1
        if name == "git" and j < len(words) and words[j] == "commit":
            return words[1:j]
    return None

def parse_command(command):
    """Return True when a shell command line runs a `git commit` invocation."""
    return commit_options(command) is not None

def target_options(opts):
    """Keep the repo-selecting options (-C, --git-dir, --work-tree) from git global options."""
    out, j = [], 0
    while j < len(opts):
        if opts[j] in ("-C", "--git-dir", "--work-tree"):
            out += [opts[j]] + [os.path.expanduser(v) for v in opts[j + 1:j + 2]]
        elif opts[j].startswith(("--git-dir=", "--work-tree=")):
            out.append(opts[j])
        j += 2 if opts[j] in FLAGS_WITH_ARG else 1
    return out

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
            elif key == "block_on" and value in BLOCK_ON:
                block_on = value
    return enabled, block_on

def check_stamp(stamp_text, digest, block_on):
    """Return a deny reason, or None when the stamp is valid for the staged diff."""
    try:
        stamp = json.loads(stamp_text) if stamp_text is not None else None
    except ValueError:
        stamp = None
    if (not isinstance(stamp, dict) or "worst_severity" not in stamp
            or stamp.get("verdict") not in VERDICTS
            or not (stamp["worst_severity"] is None or stamp["worst_severity"] in SEVERITIES)
            or not isinstance(stamp.get("diff_sha256"), str) or not SHA256.fullmatch(stamp["diff_sha256"])):
        return REVIEW_MSG
    if stamp["diff_sha256"] != digest:
        return "The staged diff changed since it was reviewed. " + REVIEW_MSG
    worst, verdict = stamp["worst_severity"], stamp["verdict"]
    blocking = worst is not None and SEVERITIES.index(worst) <= SEVERITIES.index(block_on)
    if blocking or verdict == "CHANGES NEEDED":
        return (f"The review found blocking issues (worst severity {worst}, verdict {verdict}). "
                "Fix them, restage and re-review with neral:review before committing.")
    return None

def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, timeout=30)

HOOK_MARKER = "# neral-git-hook"

def repo_opted_in(top, cwd=None, opts=()):
    """True when the target repo opted in to Neral: its work tree `top` has .neral/config.yml,
    or its git pre-commit hook is the Neral stub (contains the marker line). The hook is found
    with the same target options as the commit. An unknown target or unreadable hook counts
    as opted in, since not opted in means the commit is allowed."""
    if top and Path(top, ".neral", "config.yml").is_file():
        return True
    out = git(cwd or top, *opts, "rev-parse", "--path-format=absolute", "--git-path", "hooks/pre-commit")
    path = out.stdout.decode().strip()
    if out.returncode != 0 or not path:
        return True
    if not os.path.lexists(path):
        return False
    try:
        return HOOK_MARKER in Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return True

DIFF_ARGS = ("diff", "--cached", "--no-ext-diff", "--no-textconv", "--no-color")

def staged_digest(cwd, git_opts=(), timeout=30):
    """sha256 of the staged diff, streamed from git. Raises on a git error or timeout.
    External diff drivers, textconv and colour are turned off so the bytes are deterministic."""
    h = hashlib.sha256()
    with subprocess.Popen(["git", *git_opts, *DIFF_ARGS], cwd=cwd, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL) as proc:
        killed = threading.Event()
        timer = threading.Timer(timeout, lambda: (killed.set(), proc.kill()))
        timer.start()
        try:
            for chunk in iter(lambda: proc.stdout.read(65536), b""):
                h.update(chunk)
            code = proc.wait()
        finally:
            timer.cancel()
    if killed.is_set():
        raise subprocess.TimeoutExpired(proc.args, timeout)
    if code != 0:
        raise RuntimeError(f"git diff failed with exit code {code}")
    return h.hexdigest()

def decide(payload, env):
    """Return a deny reason for this hook payload, or None to allow."""
    command = (payload.get("tool_input") or {}).get("command", "")
    opts = commit_options(command)
    if payload.get("tool_name") != "Bash" or env.get("NERAL_REVIEW") == "off" or opts is None:
        return None
    cwd = payload.get("cwd") or os.getcwd()
    opts = target_options(opts)  # git resolves these relative to cwd, like the shell would
    if any(c in a for a in opts for c in "$`*?"):
        return TARGET_MSG
    rev = git(cwd, *opts, "rev-parse", "--show-toplevel")
    if opts and rev.returncode != 0:
        return TARGET_MSG  # an explicit target we cannot resolve fails closed
    top = rev.stdout.decode().strip()
    if any("/.claude/worktrees/" in p.replace(os.sep, "/") + "/" for p in ((top,) if opts else (cwd, top))):
        return None
    config = Path(top or cwd, ".neral", "config.yml")
    enabled, block_on = read_config(config.read_text(encoding="utf-8") if config.is_file() else "")
    if not enabled or not repo_opted_in(top, cwd, opts):
        return None  # disabled, or a repo that never opted in to Neral
    if git(cwd, *opts, "diff", "--cached", "--quiet").returncode != 1:
        return None  # nothing staged (0), or a git error (fail open)
    digest = staged_digest(cwd, opts)
    git_dir = git(cwd, *opts, "rev-parse", "--absolute-git-dir").stdout.decode().strip()
    stamp_path = Path(git_dir, "neral", "review-stamp.json")
    stamp_text = stamp_path.read_text(encoding="utf-8") if stamp_path.is_file() else None
    return check_stamp(stamp_text, digest, block_on)

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
