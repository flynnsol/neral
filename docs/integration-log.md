# Integration log: v0.1.0 end-to-end run

Run on 2026-11-09 with Neral installed from this repo and the Engram vault driving the tickets. Two real tickets went through `neral:engineer`, then the `neral:review` pipeline: T33 (README install and marketplace description) and T34 (staged-mode notes). The pipeline was also pointed at the existing hook code (commit 7e861f2) to check that it finds real defects, not only empty results.

## What was run

| Step | Result |
|---|---|
| T33 and T34 built by `neral:engineer` in worktrees | Both committed once, tests green (34) |
| `neral:review` on T34, standard profile, six lenses | 6 of 6 lenses returned no findings; verdict PASS |
| `neral:review` on T33, quiet lenses (correctness, security) | 1 finding (P1, install command); the `verifier` REFUTED it with `claude plugin install --help` output; verdict PASS |
| `neral:review` on hook code 7e861f2, quiet lenses (correctness, security, data-integrity) | 8 raw findings, 5 after dedupe; 2 P1 confirmed by `verifier` and by `tester` repro tests |

## Findings on the hook code

H1 to H5 came from the pipeline run on commit 7e861f2; H6 and H7 came from live use of the gate.

| ID | Sev | Claim | Verdict |
|---|---|---|---|
| H1 | P1 | `parse_command` misses `git commit` in subshells, `if` blocks, `bash -c`, `env`, `command`, `sudo`, `time` | CONFIRMED, repro fails on 8 forms |
| H2 | P1 | `git commit -a` and `git commit <paths>` bypass the gate; an empty index counts as "nothing staged" | CONFIRMED, repro fails |
| H3 | P2 | `git -C <dir>` and `cd` targets are ignored, so the wrong repo is checked | Below the quiet cutoff, not verified |
| H4 | P3 | A stamp missing `verdict` or `worst_severity` is accepted | Below the cutoff, not verified |
| H5 | P3 | `block_on: P3` is accepted though the schema allows only P0 to P2 | Below the cutoff, not verified |
| H6 | P1 | `git add f && git commit` in one command: the hook runs before `add` executes, the index is empty, and the gate allows the commit with no stamp | Found by running the gate live, reproduced with `decide()` |
| H7 | P3 | Any script text containing a line that starts with `git commit` trips the gate, even when no commit runs | Found live, reproduced with `parse_command` |

## Pre-commit gate, observed live

| Case | Result |
|---|---|
| `git commit -m "..."` with a change staged earlier and no stamp | Denied with the "run neral:review" instruction |
| `git add file && git commit ...` as one command | Allowed with no stamp (H6). The first commit of this log landed this way, unreviewed |
| A script that only mentions `git commit` | Denied (H7) |
| Commits by `neral:engineer` inside worktrees | Skipped by design |

The verifier noted that H1 is a guardrail gap, not a sandbox escape: the gate protects against Claude's own accidental commits, so P2 is arguable. It is kept at P1 because the fix is cheap.

## Review of the parser fixes (T35) and the design change

The pipeline review of T35 (three lenses: correctness, security, data-integrity) found more shell forms the parser misses:

- backticks and `$()` inside double quotes
- `eval`
- `xargs`
- `command -p` and `time -p`
- `bash -o pipefail -c`
- a `<<` arithmetic shift treated as a heredoc
- the attached form `git -Cdir`

These are known limits of the best-effort PreToolUse layer, not security holes: enforcement moved to a git pre-commit hook (decision D3), which git runs for every commit form. The PreToolUse hook stays as an early, friendly deny. See `docs/review-stamp.md`, "Enforcement layers".

The data-integrity lens also found a stamp-path mismatch in linked worktrees: `.git/neral/review-stamp.json` breaks where `.git` is a file. T40 fixed the docs to use `git rev-parse --git-path neral/review-stamp.json`.

## Gaps found and what to do

| # | Gap | Action | Status |
|---|---|---|---|
| 1 | Hook bypasses and false positives H1 to H7 (above) | Fix in T35 and T36 | Open |
| 2 | `engram:work` reviews with a single `reviewer` agent, not the `neral:review` pipeline | Add a rule so Claude runs `neral:review` after a ticket reaches review (T23) | Fixed in T23 (`skills/review/SKILL.md`, "With a ticket workflow") |
| 3 | Six lens passes on a 3-line docs diff is wasteful | Scale lenses to the diff: docs-only changes run `correctness` only (T23) | Fixed in T23 (`skills/review/passes.md`, "Scale to the diff") |
| 4 | Reviewers lack environment facts (the install-flag false positive) | Include `claude plugin validate` output and CLI help checks in gate hints (T23) | Fixed in T23 (`skills/review/gate.md`) |
| 5 | Worktree agents hit refusals on chained git commands and inline scripts that mention git | Tell `engineer` to run git as plain separate commands (T23) | Fixed in T23 (`agents/engineer.md`) |
| 6 | One agent stalled when a trim edit was refused and left uncommitted work | Orchestrator finishes the commit; keep tickets under the size limit | Open |
| 7 | Agents use an Opus co-author trailer when the brief asks for Sonnet | Decide on one attribution rule; not a plugin defect | Open |
| 8 | The learnings flow was not exercised | Cover it in a later run | Open |
| 9 | Parser-based enforcement cannot be complete | Enforce in a git pre-commit hook (T36, T39) | Open |

## PreToolUse input for worktree edits (NER-49)

Source: the Claude Code hooks, hooks guide and permissions docs (read 2026-11-11). This is documentation, not a captured payload: the exact `agent_type` string for a plugin agent is not confirmed.

| Question | Finding |
|---|---|
| Does the payload name the calling agent? | Tool events inside a subagent carry `agent_id` and `agent_type`. The docs example is unscoped (`Explore`), so whether a plugin agent reports `neral:engineer` or `engineer` is unconfirmed. |
| Are paths absolute? | `tool_input.file_path` for `Edit` and `Write` is always absolute (`~` and relative paths are expanded before hooks run). `cwd` is documented only as the working directory, and is absolute in every example. |
| How does a hook allow? | `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "permissionDecisionReason": "..."}}`. |
| Does a hook allow override rules? | No. A matching `deny` rule still blocks and a matching `ask` rule still prompts. In plan mode an allow on a file edit has no effect. |
| Can a plugin matcher be `Edit\|Write`? | Yes, the same matcher rules apply to a plugin's `hooks/hooks.json`. |

**Rule for NER-50: path only, with containment and exclusions.**

- **Path only.** The allow must not depend on `agent_type`, because its value for plugin agents is unconfirmed and a wrong guess would silently allow nothing. If the value is later confirmed, it can be added as an extra condition.
- **Where.** Two roots, both found with git and neither taken from a payload path string directly:
  - The **main repo** is the parent of `git rev-parse --path-format=absolute --git-common-dir`, run in the payload `cwd`. This works whether `cwd` is the main checkout or inside a linked worktree.
  - The **worktree root** is `git rev-parse --show-toplevel` run in the nearest existing ancestor directory of the realpath of `file_path`. It must be a linked worktree (its git dir differs from its common dir) whose common dir has the same realpath as the main repo's, and it must sit directly under the main repo's `.claude/worktrees/` or `.worktrees/` (Claude Code's own agent worktrees, and the worktree-per-ticket layout some repos use, such as dioxus-atelier-ui). The realpath of that container directory must itself be inside the realpath of the main repo, so a symlinked `.worktrees` pointing elsewhere is refused.
  - Anchoring on the main repo from `cwd` means the allow works when an agent's `cwd` is the main checkout, and refuses worktrees that belong to some other repo. Anything that does not match falls through to the normal prompt.
- **Containment.** Take the realpath of `file_path` (for a new file, of its deepest existing ancestor plus the rest) and of the worktree root, and test containment in the worktree root with a separator-aware check (`os.path.commonpath` or `startswith(root + os.sep)`). `..` escapes, sibling names like `.worktrees-evil` and symlinks that leave the root all fall through to the normal prompt.
- **Exclusions.** A best-effort denylist, not a guarantee. Never auto-allow files that can run code, change permissions or steer agents: `.claude/`, `.git*` (including `.gitmodules` and `.gitattributes`), `.mcp.json`, `.github/`, `.husky/`, `.githooks/`, `.envrc`, `.direnv/`, `.env*`, `.vscode/`, `.idea/`, `.devcontainer/`, `.cargo/`, `.npmrc`, `.yarnrc*`, `.mise.toml`, `.tool-versions`, `.pre-commit-config.yaml`, `CLAUDE*.md` and `AGENTS.md`. Match on any path component, case-insensitively, relative to the worktree root (so the worktree's own location does not trigger them), and against both the lexical path and the realpath: if either matches, fall through. This stops an in-worktree symlink such as `docs -> .claude` from smuggling a write past the list. Tests cover a symlinked directory pointing at `.claude/` and a symlinked file pointing at `.envrc`. Residual risk: a file type missing from the list.
- **Fail closed.** Emit an allow only when every check positively succeeds. A `git` failure, malformed JSON, a missing or non-string `file_path` or `cwd`, a relative path, a realpath error or any exception exits 0 with no output, so the normal prompt applies. Each case gets a test. Known residual risks: hardlinks (realpath does not detect them) and the window between the check and the write if a symlink is swapped.
- **Rules still win.** A matching `deny` or `ask` rule overrides the allow, as the table above says.
