---
description: Show or change Neral review settings in .neral/config.yml and manage learned rules
argument-hint: [profile <quiet|standard|strict> | rule "<glob>: <text>" | check "<rule>" | ignore <glob> | lenses <list> | test <cmd> | rounds <n> | precommit <on|off> | precommit profile <quiet|standard|strict> | precommit lenses <list> | precommit block <P0|P1|P2> | precommit install | precommit uninstall | learnings | init | free-form request]
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(mkdir:*), Bash(diff:*), Bash(git ls-files:*), Bash(python3:*)
---

# /neral:config

Show or change Neral settings. Arguments: `$ARGUMENTS`

Reference: `docs/config-schema.md` (keys, allowed values, defaults), `templates/config.yml` (starting file), `skills/review/learnings.md` (learning entry format and approval flow).

## Parse the arguments

Match the first word. If nothing matches and there are arguments, treat them as free-form English (see the last section).

| Arguments | Action |
|-----------|--------|
| none | Show the effective config |
| `profile <quiet\|standard\|strict>` | Set `profile` |
| `rule "<glob>: <instructions>"` | Append to `path_instructions` (split at the first `: `) |
| `check "<rule>"` | Append to `custom_checks` with a generated short kebab-case `name` (max 4 words, unique) |
| `ignore <glob>` | Set `ignore`. Replaces the default list, so ask first whether to replace or add to the current list |
| `lenses <list>` | Set `lenses` (comma or space separated) |
| `test <command>` | Set `test_command` |
| `rounds <n>` | Set `fix_loop.max_rounds` |
| `precommit on` | Set `precommit.enabled: true` |
| `precommit off` | Set `precommit.enabled: false` |
| `precommit profile <quiet\|standard\|strict>` | Set `precommit.profile` |
| `precommit lenses <list>` | Set `precommit.lenses` (comma or space separated) |
| `precommit block <P0\|P1\|P2>` | Set `precommit.block_on` |
| `precommit install` | Install the git pre-commit hook in this repo (see the section below) |
| `precommit uninstall` | Remove the Neral git pre-commit hook from this repo |
| `learnings` | Review pending proposals |
| `init` | Create `.neral/config.yml` |

## No arguments: show the effective config

Read `.neral/config.yml` and `.neral/learnings.md` if present. Print a short table with one row per key (`profile`, `path_instructions`, `custom_checks`, `ignore`, `test_command`, `lenses`, `fix_loop.max_rounds`):

| Key | Value | Source |
|-----|-------|--------|

Source is `default` (key absent, default from the schema), `.neral/config.yml`, or `learned from .neral/learnings.md` (a learned rule applies to that key and the config does not override it). Summarize long lists by count. End with the number of approved learnings (entries in `learnings.md`) and pending proposals (entries in `.neral/proposed.md`). A missing file counts as 0.

Then show the `precommit` block the same way, one row per key (`precommit.enabled`, `precommit.profile`, `precommit.lenses`, `precommit.block_on`) with its value and source (`default` or `.neral/config.yml`). Below it, one line: `Pre-commit gate: on` when `precommit.enabled` is `true`, otherwise `Pre-commit gate: off`. Then one more line from `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/install_git_hook.py" status`: `Git hook: installed` or `Git hook: not installed`. Add two notes: `NERAL_REVIEW=off` bypasses the gate for a session, and the Claude Code hook only covers commits Claude makes; install the git hook (`precommit install`) to enforce the review for every commit, terminal commits included. See `docs/review-stamp.md`.

## Rules for every write

1. Validate against `docs/config-schema.md`. Reject an invalid value and list the allowed options, for example: `profile must be one of: quiet, standard, strict`. Checks: `profile` enum; `lenses` each one of `correctness`, `security`, `data-integrity`, `tests`, `performance`, `maintainability`; `rounds` an integer >= 1; `precommit` takes `on` or `off` (`precommit must be one of: on, off, profile, lenses, block`); `precommit profile` one of `quiet`, `standard`, `strict` (`precommit.profile must be one of: quiet, standard, strict`); `precommit lenses` each one of `correctness`, `security`, `data-integrity`, `tests`, `performance`, `maintainability` (`precommit.lenses must each be one of: correctness, security, data-integrity, tests, performance, maintainability`); `precommit block` one of `P0`, `P1`, `P2` (`precommit.block_on must be one of: P0, P1, P2`); `rule` needs a glob and non-empty instructions; `check` names are unique; `ignore` entries are globs. Write nothing on failure.
2. Edit the YAML in place. Preserve every existing comment and the key order. Change only the targeted key. For `precommit` subcommands, change only the matching key inside the `precommit:` block; if the block is missing, add it with only that key. Do not reformat or regenerate the file. A commented-out example (such as `# test_command:`) stays; add the real key beside it.
3. Show a unified diff of the change and ask for a yes. Write only after an explicit yes.
4. Create `.neral/` if it is missing. If `config.yml` is missing, create it from `templates/config.yml` as part of the same diff.
5. Never touch anything outside `.neral/`, except that `precommit install` and `precommit uninstall` write or remove the repository's `pre-commit` git hook through the installer script.

## `precommit install` and `precommit uninstall`

Run these from the repository root (the repo the user is working in). They do not edit `.neral/config.yml`.

1. `precommit install`: run `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/install_git_hook.py" install` and show its output. It writes a small `pre-commit` stub in the repo's hooks directory (respecting `core.hooksPath` and linked worktrees) that runs `hooks/git_pre_commit.py`.
2. `precommit uninstall`: run `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/install_git_hook.py" uninstall` and show its output. It removes the hook only if it is the Neral stub.
3. Explain after installing: the hook enforces the review stamp for every commit form (`commit -a`, paths, chained `add` and `commit`, terminal commits); `git commit --no-verify` skips it; set `NERAL_REVIEW=off` to bypass it for a session.
4. A `pre-commit` hook that is not Neral's is never overwritten. If the installer refuses (exit code 2), show its message and the line it suggests for chaining by hand; do not edit the foreign hook yourself.
5. The stub warns and allows the commit when the plugin script has moved (for example after a plugin update); re-run `precommit install` to refresh the path.

## `learnings`

1. Read `.neral/proposed.md`. If it is missing or empty, say there are no pending proposals and stop.
2. List the entries. For each one, show it as a diff of `.neral/learnings.md` (the entry as an added block with `status: approved`) and ask: approve, edit or reject.
3. Approve: append the entry to `.neral/learnings.md` with `status: approved` and remove it from `proposed.md`. Create `learnings.md` if missing.
4. Edit: apply the user's wording, show the diff again, ask again.
5. Reject: remove it from `proposed.md`. Write nothing to `learnings.md`.
6. Delete `proposed.md` when no entries are left. Never write `learnings.md` without approval; follow `skills/review/learnings.md` for the entry format.

## `init`

1. If `.neral/config.yml` already exists, say so and stop. Suggest the other subcommands.
2. Ask three questions: the profile (`quiet`, `standard` or `strict`; default `standard`), the test command (optional), and paths to ignore (optional globs, added to the default ignore list).
3. Validate the answers. Create `.neral/` and `.neral/config.yml` from `templates/config.yml`, applying the answers in place. Show the resulting file as a diff against the template and get a yes before writing.

## Free-form English

For input like "be stricter on the payments folder":

1. Interpret it into the matching change (here: a `path_instructions` entry for `payments/**`, or `profile: strict` if it is repo-wide). If it is ambiguous, ask one short question.
2. Restate the interpretation in one sentence, then show the unified diff.
3. Validate, then ask for a yes. Write only after the yes. If the user says no, ask what to change; never write a guess.
