# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-10

### Added

- Four subagents:
  - `engineer` (opus): implements one ticket test-first inside its `touches`, in one commit; runs git as plain separate commands.
  - `reviewer` (sonnet, read-only): reviews a diff through one lens and returns findings as JSON.
  - `verifier` (sonnet, read-only): tries to refute one finding and returns `CONFIRMED`, `REFUTED` or `INCONCLUSIVE` with evidence.
  - `tester` (sonnet): writes failing repro tests or tests for a diff; test files only.
- `neral:review` pipeline skill:
  - Steps: context pack, deterministic gate (tests, linters, type checks and `claude plugin validate` output as hints), parallel lens passes, verification, ranked P0 to P3 report with merge-risk score and verdict, capped fix loop.
  - Lens briefs for `correctness`, `security`, `data-integrity`, `tests`, `performance` and `maintainability`; lens set scaled down for docs-only and tiny diffs, recorded in the report's Lenses line.
  - Staged mode: reviews `git diff --cached` with the `precommit` settings, skips the fix loop and writes a review stamp.
  - Fix loop: fix briefs to `engineer` agents, incremental rescan, stop and escalation rules, capped by `fix_loop.max_rounds`.
  - Learnings approval flow: proposals go to `.neral/proposed.md` and reach `.neral/learnings.md` only after human approval.
  - Ticket workflow support: ticket text, `touches` and Acceptance checks feed the report's checks.
- `.neral/config.yml` (profile, lenses, path instructions, custom checks, ignore, test command, fix loop, `precommit` block) and `.neral/learnings.md`, with `templates/config.yml` and the schema in `docs/config-schema.md`.
- `/neral:config` command: show the effective config, `init`, setting subcommands, `precommit` on/off/profile/lenses/block, `precommit install` and `precommit uninstall` for the git hook, `learnings` review, and free-form requests. Every write shows a diff and waits for approval.
- Pre-commit gate:
  - Git pre-commit hook (`hooks/git_pre_commit.py`, installer `hooks/install_git_hook.py`) that enforces the review stamp for every commit form; never overwrites a foreign hook or follows a symlink.
  - Claude Code `PreToolUse` hook (`hooks/precommit_gate.py`) as an early deny for Claude's commits.
  - Review stamp (`docs/review-stamp.md`) tied to the sha256 of the staged diff, stored at `git rev-parse --git-path neral/review-stamp.json`.
  - Bypasses: `NERAL_REVIEW=off`, `precommit.enabled: false`, agent worktrees under `.claude/worktrees/`, history replays, nothing staged; fails open on hook errors.
- Shared finding schema and report format (`docs/finding-schema.md`) and an example ticket brief.
- Contract tests for the agents, hooks, installer and version agreement (`python3 -m unittest discover -s tests -t tests`).

### Known limits

- `git commit --no-verify` skips the git pre-commit hook; a terminal commit with it is not checked.
- The Claude Code hook parses shell text best-effort and can miss exotic command forms.
- The review stamp is advisory and not tamper-proof: anyone with write access to the git directory can forge it.
- Only commits are gated, not pushes.
