---
name: review
description: Review a diff, branch, PR or finished ticket for bugs before merge. Use when the user asks to review changes, check a branch or pull request, or verify a completed ticket before merging. Runs a staged pipeline (context pack, deterministic gate, parallel lens passes, verification, report, optional fix loop) and reports only evidenced findings.
---

# review

Review a change for bugs before merge. The output is a report that follows `docs/finding-schema.md`.

## Rules

- Run this skill in the main session. Subagents cannot spawn subagents, so the orchestrator (you) launches every agent itself.
- The orchestrator launches the `reviewer`, `verifier`, `tester` and `engineer` agents.
- Review is independent of the author. The reviewer never gets the author's reasoning, commit-message rationale or chat history. It gets the context pack only.
- Only evidenced findings reach the report. A finding without evidence (code excerpt, command output or failing test) is dropped.

## Pipeline

Follow the steps in order. Each step lives in its own file in this folder.

1. **Context pack**: gather the diff and related context. See [context-pack.md](context-pack.md).
2. **Deterministic gate**: run tests, linters and type checks before any model pass and pass their output on as hints. See [gate.md](gate.md).
3. **Parallel lens passes**: launch one `reviewer` per lens in parallel on the context pack. See [passes.md](passes.md).
4. **Verify, score and report**: launch `verifier` (and `tester` where a finding needs a failing test) on each finding, then score and write the report. See [verify.md](verify.md) and [report.md](report.md).
5. **Fix loop**: hand confirmed findings to `engineer`, then re-check, up to `fix_loop.max_rounds`. Skipped in staged mode. See [fix-loop.md](fix-loop.md).
6. **Learnings proposals**: propose durable rules from confirmed findings for human approval. See [learnings.md](learnings.md).

## Staged mode

Use staged mode when the user or the pre-commit gate asks to review staged changes before a commit. It runs the same pipeline with these differences:

- **Diff source**: `git diff --cached` (the staged changes), not a branch range. See [context-pack.md](context-pack.md).
- **Settings**: profile, lenses and severity cutoff come from the `precommit` block in `.neral/config.yml`, not the top-level `profile` and `lenses` keys. Defaults: profile `quiet`; lenses `correctness`, `security`, `data-integrity`; `block_on: P1`. `precommit.lenses` is the enabled lens set for step 3, and `precommit.profile` sets the cutoff in step 4.
- **No fix loop**: staged mode never runs the fix loop (step 5). Report the findings and stop. The user or engineer fixes them, restages, and asks for a new review.
- **Verification**: runs as normal (step 4).
- **Stamp**: the review ends by writing the review stamp at the path printed by `git rev-parse --git-path neral/review-stamp.json` (do not hard-code the path: in a linked worktree `.git` is a file). See [report.md](report.md) (Stamp section) and `docs/review-stamp.md`.

## With a ticket workflow

When a ticket reaches review in a ticket workflow (for example Engram's work skill), run this pipeline on the ticket's diff instead of a single `reviewer`:

- Pass the ticket text, its `touches` and its Acceptance checks into the context pack, so the report's checks run against them.
- Use the configured `profile` (default `standard`) for ticket diffs, not the `precommit` settings. The `precommit` settings apply only in staged mode.

## References

- `docs/finding-schema.md`: finding record and report format.
- `docs/config-schema.md`: `.neral/config.yml` and `.neral/learnings.md`.
- `docs/review-stamp.md`: review stamp fields, hash command and validity rule.
