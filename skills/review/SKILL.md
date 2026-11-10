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
2. **Deterministic gate**: run the mechanical checks (tests, touches, size limit) before any model pass. See [gate.md](gate.md) (added in a later ticket).
3. **Parallel lens passes**: launch one `reviewer` per lens in parallel on the context pack. See [passes.md](passes.md) (added in a later ticket).
4. **Verify, score and report**: launch `verifier` (and `tester` where a finding needs a failing test) on each finding, then score and write the report. See [verify.md](verify.md) and [report.md](report.md) (added in a later ticket).
5. **Fix loop**: hand confirmed findings to `engineer`, then re-check, up to `fix_loop.max_rounds`. See [fix-loop.md](fix-loop.md) (added in a later ticket).
6. **Learnings proposals**: propose durable rules from confirmed findings for human approval. See [learnings.md](learnings.md) (added in a later ticket).

## References

- `docs/finding-schema.md`: finding record and report format.
- `docs/config-schema.md`: `.neral/config.yml` and `.neral/learnings.md`.
