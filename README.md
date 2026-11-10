<p align="center">
  <img src="assets/banner.png" alt="Neral" width="100%">
</p>

# Neral

A Claude Code plugin of `engineer`, `reviewer`, `verifier` and `tester` subagents, plus an evidence-first review pipeline.

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Status: v0.1.0](https://img.shields.io/badge/status-v0.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3-blue.svg)

**Status:** `v0.1.0`, the first release.

## Description

One agent that writes code, reviews it and approves it marks its own homework. Neral splits the work into small roles: one agent implements, others review the diff through a single lens each, and a finding only reaches the report if it survives an attempt to refute it with evidence. It works on its own and honours ticket conventions (`role`, `touches`, Acceptance) so tools such as Engram can dispatch work to it.

## Install

In Claude Code 2.1.275 or later, install in one step:

```text
/plugin install neral --marketplace flynnsol/neral
```

On older versions, add the marketplace first, then install the plugin:

```text
/plugin marketplace add flynnsol/neral
/plugin install neral@neral
```

## Agents

| Agent | Model | Tools | What it does |
| ----- | ----- | ----- | ------------ |
| `engineer` | opus | Read, Grep, Glob, Edit, Write, Bash | Implements one ticket test-first inside its allowed paths, in one commit. |
| `reviewer` | sonnet | Read-only (Read, Grep, Glob, Bash) | Reviews a diff through one lens and returns findings as JSON. Never edits files. |
| `verifier` | sonnet | Read-only (Read, Grep, Glob, Bash) | Tries to refute one finding from the code; returns `CONFIRMED`, `REFUTED` or `INCONCLUSIVE`. |
| `tester` | sonnet | Read, Grep, Glob, Edit, Write, Bash | Writes failing repro tests or tests for a diff. Touches test files only. |

## How the review works

Ask Claude to review a diff, a branch, a PR or a finished ticket, and the `neral:review` skill runs in the main session:

| Step | What happens |
| ---- | ------------ |
| 1. Context pack | Gathers the diff, callers of changed symbols, related tests, project rules and `.neral/` config and learnings. |
| 2. Gate | Runs tests, linters and type checks first; their output goes to reviewers as hints, not findings. |
| 3. Lens passes | One `reviewer` per lens in parallel: `correctness`, `security`, `data-integrity`, `tests`, `performance`, `maintainability`. Small and docs-only diffs run fewer lenses. |
| 4. Verify | A `verifier` (and a `tester` where a failing test is needed) tries to refute each finding. Refuted findings are dropped. |
| 5. Report | Ranked findings P0 to P3, a merge-risk score from 0 to 5 (5 = safest), checks run (Acceptance, touches, size) and a verdict: `PASS`, `PASS WITH NOTES` or `CHANGES NEEDED`. |
| 6. Fix loop | Confirmed findings go to `engineer` agents as fix briefs, then the new diff is re-checked, up to `fix_loop.max_rounds` (default 3). |

After a review, Neral may propose durable rules from confirmed findings or your feedback. Proposals wait in `.neral/proposed.md` until you approve them.

Severity levels:

| Level | Meaning |
| ----- | ------- |
| P0 | Critical: security exploit, data loss, severe crash |
| P1 | Defect: wrong data, race, broken contract |
| P2 | Quality: missing tests, dead code, naming |
| P3 | Nit |

**Staged mode** reviews `git diff --cached` before a commit. It uses the `precommit` settings (default profile `quiet`, lenses `correctness`, `security`, `data-integrity`), skips the fix loop and ends by writing a review stamp for the pre-commit gate.

The finding and report format is in [docs/finding-schema.md](docs/finding-schema.md).

## Configuration

All settings are optional. With no `.neral/` directory, defaults apply.

| File | Purpose |
| ---- | ------- |
| `.neral/config.yml` | Review settings: `profile` (`quiet`, `standard`, `strict`), `lenses`, `path_instructions`, `custom_checks`, `ignore`, `test_command`, `fix_loop.max_rounds`, `precommit`. |
| `.neral/learnings.md` | Learned rules. Holds only entries you approved. |
| `.neral/proposed.md` | Pending proposals. Never applied until approved. |

Change settings with `/neral:config`. Every write shows a diff and waits for a yes.

| Command | Effect |
| ------- | ------ |
| `/neral:config` | Show the effective config and where each value comes from |
| `/neral:config init` | Create `.neral/config.yml` from the template |
| `/neral:config profile <quiet\|standard\|strict>` | Set the profile |
| `/neral:config lenses <list>` | Set the enabled lenses |
| `/neral:config rule "<glob>: <text>"` | Add a path instruction |
| `/neral:config check "<rule>"` | Add a custom check |
| `/neral:config ignore <glob>` | Set ignored paths |
| `/neral:config test <cmd>` | Set the test command |
| `/neral:config rounds <n>` | Set the fix loop round cap |
| `/neral:config precommit <on\|off>` | Turn the pre-commit gate on or off |
| `/neral:config precommit profile\|lenses\|block ...` | Tune the pre-commit review |
| `/neral:config precommit install\|uninstall` | Install or remove the git pre-commit hook |
| `/neral:config learnings` | Approve, edit or reject pending proposals |

Free-form requests also work, for example `/neral:config be stricter on the payments folder`. The full schema is in [docs/config-schema.md](docs/config-schema.md).

## Pre-commit gate

A commit needs a valid review stamp: a staged-mode review of the exact staged diff with no surviving finding at or above `precommit.block_on` (default `P1`) and no failed check.

| Layer | Role |
| ----- | ---- |
| Git pre-commit hook | Installed with `/neral:config precommit install`. Git runs it for every commit form, including `commit -a`, commits with paths, chained `add` and `commit`, and terminal commits. This is the layer that enforces the stamp. |
| Claude Code hook | A `PreToolUse` hook that denies Claude's `git commit` early, before the command runs. It parses shell text best-effort. |

- Set `NERAL_REVIEW=off` to bypass the gate for a session, or run `/neral:config precommit off`.
- `git commit --no-verify` skips the git hook; a terminal commit with it is not checked.
- Commits by agents in worktrees under `.claude/worktrees/` are skipped.
- Merges, cherry-picks, reverts and rebases are skipped.

Stamp fields and the validity rule are in [docs/review-stamp.md](docs/review-stamp.md).

## Using with Engram

Neral works with any ticket that carries a `role`, a `touches` list and Acceptance checks.

- `engram:work` picks the agent for each ticket by its `role` (`engineer`, `tester`, and so on).
- The `engineer` stays inside `touches`, works test-first and makes one commit.
- When a ticket reaches review, run `neral:review` on its diff. The ticket text, `touches` and Acceptance checks go into the context pack, so the report checks against them.

See [docs/example-ticket-brief.md](docs/example-ticket-brief.md) for a sample brief.

## Testing

The contract tests use the Python standard library only:

```bash
python3 -m unittest discover -s tests -t tests
```

## License

MIT. See [LICENSE](LICENSE).
