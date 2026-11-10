# Step 2: Deterministic gate

Run deterministic tools on the change and pass their output to the reviewers as hints. A hint is a lead to adjudicate, never a finding.

## What to run

1. **Tests.** Use `test_command` from `.neral/config.yml` if set. Otherwise detect one from the repo: `package.json` scripts (`test`), `Makefile` (`test` target), `pyproject.toml` (pytest), `Cargo.toml` (`cargo test`), or `python3 -m unittest discover`. Run it once.
2. **Linters and type checkers already configured in the repo** (for example ruff, eslint, clippy, tsc, mypy, shellcheck). Detect them from config files or scripts. Do not run a tool the repo does not configure. Limit to the changed files where the tool supports it (`ruff check <files>`); otherwise run it on the project.

## Rules

- Take the changed-file list from the context pack. Drop files matching `ignore` globs before running tools, and drop hints for ignored files.
- Read-only. Never install dependencies, never modify files, never use autofix flags (`--fix`, `--write`, `-w`). If a tool cannot run without installing or writing, skip it and say so.
- Time limit about 5 minutes per tool. On timeout, stop the tool and record it as `timeout`.
- A missing, slow or failing tool never aborts the review. Record it and continue to the next tool.

## Capture per tool

- Command run, exit status, and trimmed relevant output (cap at about 40 lines; keep the failing lines, drop passing noise).
- Map each message to `file:line` when the output gives it. Otherwise leave `file` and `line` empty.

## Output: gate hints block

```
gate hints:
- tool: ruff
  command: ruff check src/a.py
  status: exit 1
  file: src/a.py
  line: 12
  message: F821 undefined name `x`
summary:
  ran: ruff, unittest
  skipped: eslint (not configured), tsc (needs install)
  failed to run: mypy (timeout)
```

- One entry per message: `tool`, `command`, `status` (`pass`, `exit <n>`, `timeout`, `not run`), `file`, `line`, `message`.
- The summary lists which tools ran, which were skipped and why, and which failed to run.
- A failing test run is a strong hint: include the failing test names and assertion lines, and mark it prominently.

## Hard rule

Reviewers must adjudicate each hint against the code. A tool message alone is never a finding; it becomes one only with the reviewer's own evidence under `docs/finding-schema.md`. A clean gate does not mean the change is clean.
