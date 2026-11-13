<p align="center">
  <img src="assets/banner.png" alt="Neral" width="100%">
</p>

# Neral

A Claude Code plugin of `engineer`, `reviewer`, `verifier` and `tester` subagents, plus an evidence-first review pipeline, and `architect` and `product-manager` agents that challenge a draft plan before work starts.

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3-blue.svg)

See the [CHANGELOG](CHANGELOG.md) for the current version and release notes.

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

## Set up a repo

Installing the plugin alone changes nothing in a repo: no config, no git hook and no gate. Run this once in each repo you want Neral to review:

```text
/neral:config init
```

It asks for a profile, a test command and paths to ignore, then writes `.neral/config.yml`. It then offers to install the git pre-commit hook. Say yes (recommended): the hook enforces the review stamp for every commit form. This is what turns the [Pre-commit gate](#pre-commit-gate) on for that repo.

Git hooks are not versioned, so each fresh clone needs the hook installed again with `/neral:config precommit install`.

First run:

1. Install the plugin.
2. Run `/neral:config init` in your repo.
3. Ask Claude to review a diff or ticket (`neral:review`).
4. Commit. The gate requires a staged-mode review stamp, so ask Claude to review the staged changes first.

## Agents

| Agent | Model | Tools | What it does |
| ----- | ----- | ----- | ------------ |
| `engineer` | opus | Read, Grep, Glob, Edit, Write, Bash | Implements one ticket test-first inside its allowed paths, in one commit. |
| `reviewer` | sonnet | Read-only (Read, Grep, Glob, Bash) | Reviews a diff through one lens and returns findings as JSON. Never edits files. |
| `verifier` | sonnet | Read-only (Read, Grep, Glob, Bash) | Tries to refute one finding from the code; returns `CONFIRMED`, `REFUTED` or `INCONCLUSIVE`. |
| `tester` | sonnet | Read, Grep, Glob, Edit, Write, Bash | Writes failing repro tests or tests for a diff. Touches test files only. |
| `architect` | opus | Read-only (Read, Grep, Glob, Bash) | Challenges a draft plan on its model, database and view architecture, grounded in the repo. Never edits files. |
| `product-manager` | opus | Read-only (Read, Grep, Glob, Bash) | Pushes back on unrealistic requirements and timelines, and checks the plan suits sub-agent engineers. Never edits files. |

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

## Challenging a plan

Ask Claude to challenge a draft plan, epic or feature before it is accepted, and the `neral:challenge` skill runs in the main session:

| Step | What happens |
| ---- | ------------ |
| 1. Brief | Passes the plan as text, with the repo path and optional project rules. |
| 2. Agents | Runs `architect` and `product-manager` in parallel. Both are read-only. |
| 3. Merge | Drops challenges without evidence, dedupes overlaps and ranks the rest `blocker`, then `major`, then `minor`. |
| 4. Ask | Puts the ranked list to you as questions, with each agent's assumptions. You decide. |

The agents challenge only when something warrants it. Otherwise they return `no_concerns`, and the skill says so instead of inventing questions. The skill never rewrites the plan.

The report format is in [docs/pushback-schema.md](docs/pushback-schema.md).

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
| `/neral:config init` | Create `.neral/config.yml` from the template and offer to install the git pre-commit hook |
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

### When the gate is on

The gate is opt-in per repo. A repo is gated only when one of these holds:

- it has `.neral/config.yml` that does not set `precommit.enabled: false`, or
- the Neral git hook stub is installed (`/neral:config precommit install`).

A repo with neither is never gated: the git hook only runs where it is installed, and the Claude Code hook allows commits in repos that have not opted in.

Installing the plugin never installs a git hook. Git hooks live in each repo's `.git/hooks`, and a plugin cannot write there, so install the hook once per repo and once per fresh clone.

- Opt in: run `/neral:config init`, which writes `.neral/config.yml` and offers to install the git hook (on an existing config it reports the hook status and offers the install), or run `/neral:config precommit install`.
- Opt out: run `/neral:config precommit off`, set `NERAL_REVIEW=off` for a session, or remove the hook with `/neral:config precommit uninstall`.

### Bypasses

- Set `NERAL_REVIEW=off` to bypass the gate for a session, or run `/neral:config precommit off`.
- `git commit --no-verify` skips the git hook; a terminal commit with it is not checked.
- Commits by agents in worktrees under `.claude/worktrees/` are skipped.
- Merges, cherry-picks, reverts and rebases are skipped.

Stamp fields and the validity rule are in [docs/review-stamp.md](docs/review-stamp.md).

## Worktree edits

A second `PreToolUse` hook, for `Edit` and `Write`, auto-allows edits to files inside the repo's own linked worktrees, the ones directly under `.claude/worktrees/` or `.worktrees/`. Agents working in a worktree then do not prompt for every edit.

- It only skips the prompt. A matching `deny` or `ask` permission rule still wins.
- It never allows paths that escape the worktree (`..`, symlinks, hardlinks), worktrees of other repos, or files that can run code or steer agents, such as `.claude/`, `.git*`, `.env*`, `.envrc`, `.github/`, `.vscode/`, `CLAUDE*.md` and `AGENTS.md`. The full list is in `hooks/worktree_allow.py`.
- Anything it cannot check gets the normal prompt.
- It only acts in repos that opted in to Neral, the same opt-in as the pre-commit gate: the main checkout has `.neral/config.yml`, or the Neral git hook is installed. Elsewhere it does nothing.
- To turn it off, do not opt the repo in, or remove the `Edit|Write` entry from `hooks/hooks.json`.
- Set `NERAL_DEBUG=1` to print why an edit was not auto-allowed to stderr.

If you write your own permission rules instead: in Claude Code rules `//path` is an absolute path and `/path` is relative to the settings file. So `Edit(/home/x/..)` never matches; write `Edit(//home/x/..)`.

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
