# Step 5: Fix loop

Fix surviving findings and re-check them, up to a round cap.

## When to run

- Run only when the verdict is `CHANGES NEEDED`.
- Run on `PASS WITH NOTES` only if the user asks to fix the notes.
- Otherwise skip this step and return the report.
- Never run in staged mode (see [SKILL.md](SKILL.md)). Report the findings and stop. The user or engineer fixes them, restages, and asks for a new review.

## Inputs

- The final report and fix briefs from [report.md](report.md) (section 7).
- `fix_loop.max_rounds` from config (default `3`).
- The last reviewed commit (the commit the report covers).

## A round

1. Group the fix briefs by file. Briefs that touch the same files go to the SAME `engineer` in one combined brief, so edits do not collide.
2. Launch one `engineer` per group, each in its own git worktree. Launch independent groups in parallel, in a SINGLE message with several Agent calls.
3. Each engineer fixes only its findings, test-first, and makes one commit (see `agents/engineer.md`).
4. Merge the engineer commits into the working branch. If an engineer reports scope widening (a file outside its touches, or a change too big for one commit), stop and escalate.
5. Rescan incrementally. Run steps 1-4 on ONLY the diff between the last reviewed commit and HEAD, plus the callers of what changed. Do not re-review unchanged code. Carry forward findings that are already `CONFIRMED` and still unfixed; do not re-verify them.
6. Rebuild the report from the carried and new findings, re-run the pre-merge checks, and set the new last reviewed commit to HEAD.

## Independence

- Reviewers, verifiers and testers get only the new diff and the context pack. Never give them the engineer's reasoning, report or commit-message rationale.

## Stop conditions

- Stop early with success when the verdict is `PASS`, or `PASS WITH NOTES` with no P0/P1, and all checks pass.
- Stop and escalate when any of these holds:
  - the round count reaches `fix_loop.max_rounds` and the verdict is still `CHANGES NEEDED`;
  - a round makes no progress: the same finding survives twice after an identical fix attempt;
  - an engineer reports scope widening.

## Escalation message

Tell the user, filling in the values:

"Review loop stopped after N rounds. Remaining: <list of findings with severity and location>. Last verdict: <verdict>. Options: fix manually, raise fix_loop.max_rounds, or accept with notes."

## Output

- The final report (shape in `docs/finding-schema.md`).
- A one-line round history, for example: `Rounds: 1 (fixed 3, remaining 1); 2 (fixed 1, remaining 0)`.
