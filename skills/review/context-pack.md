# Step 1: Context pack

Build one compact pack that every later step uses. Gather each source below, then hand the pack (never the author's reasoning) to the reviewers.

## Sources

| Source | How to gather |
|---|---|
| Diff | `git diff <base>...HEAD`, plus `git diff --name-only <base>...HEAD` for the changed files. Take `<base>` from the user, the PR target, or the default branch. |
| Callers of changed symbols | For each changed function, class or exported name, grep (or use LSP find-references) for its uses elsewhere. One hop only: direct callers, not callers of callers. |
| Related tests | Tests that reference a changed file or a changed symbol. Grep the test directories for the file's module name and the symbol names. |
| Project rule files | Read those that exist: `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md`. |
| Neral config | `.neral/config.yml`: `profile`, the `path_instructions` whose glob matches a changed path, `custom_checks`, and `ignore`. |
| Learnings | `.neral/learnings.md`: entries with `status: approved` whose `path` matches a changed path (or that have no `path`). Skip `proposed` and `rejected`. |
| Ticket | If a ticket exists, include its text, `touches` and Acceptance. Skip if none. |

## Staged mode

In staged mode (see [SKILL.md](SKILL.md)) gather the diff with `git diff --cached` and the changed files with `git diff --cached --name-only`, instead of the `<base>...HEAD` range. Gather callers and related tests as usual. The ticket is optional: include it if one is given, otherwise skip it. Read `profile` and `lenses` from the `precommit` block, not the top-level keys.

## Rules

- Apply the `ignore` globs first: drop every matching file from the changed-file list, the diff and the other sources.
- If `.neral/` is missing, use the defaults from `docs/config-schema.md` (profile `standard`, default `ignore`, no path instructions, no custom checks, no learnings). A missing file or key falls back to its default the same way.
- `config.yml` wins over `learnings.md`. If a learning conflicts with the config, drop the learning.
- Keep the pack compact: include excerpts (the changed hunks, the call sites, the relevant test cases), not whole files.
