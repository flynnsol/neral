# Step 4b: Score and report

Turn the verified findings into the final review report. The format is the example in `docs/finding-schema.md`; reproduce its shape exactly.

## Inputs

- The verified findings list and Dropped list from [verify.md](verify.md).
- The effective config (`profile`, `custom_checks`) and the ticket, if any.

## 1. Severity cutoff

Read `profile` from config (default `standard`; in staged mode, `precommit.profile`, default `quiet`). Keep only findings at or above the cutoff:

| Profile | Reported |
|---|---|
| `quiet` | P0-P1 |
| `standard` | P0-P2 |
| `strict` | P0-P3 |

Omit findings below the cutoff from the counts, ranking and fix briefs.

## 2. Pre-merge checks

Each check is `pass` or `fail: <reason>`.

- **Ticket Acceptance**: run each Acceptance check from the ticket. Fail if any fails. No ticket: skip and write `skipped (no ticket)`.
- **Touches**: every changed file is within the ticket's declared touches. Fail and name the undeclared files. No ticket: skip.
- **Size limit (200 lines, 5 files)**: pass only if the change is under 200 changed lines and at most 5 files; otherwise fail with the actual numbers.
- **Custom checks**: for each `custom_checks` entry, judge its `instructions` against the diff. Report `pass` or `fail: <reason>`, with the entry `name` as the check name.

## 3. Merge-risk score

Start at 5. Subtract 2 per surviving P0, 1 per surviving P1 and 1 per failed check. Floor at 0. If any P0 survives, cap the score at 1. Skipped checks do not count.

## 4. Verdict

- `CHANGES NEEDED`: any P0 or P1 survives, or any check fails.
- `PASS WITH NOTES`: only P2/P3 findings survive.
- `PASS`: no findings survive and all checks pass.

## 5. Rank

Sort findings by severity (P0 first), then confidence (high first). Renumber the `#` column from 1; keep each finding's `id`. Flag INCONCLUSIVE findings as unverified in the Verdict column.

## 6. Write the report

Use this shape: an H1 `# Review: <ticket id and title, or branch>`; the lines `**Verdict:**`, `**Merge-risk score:** N/5 (5 = safest to merge)` and `**Profile:** <profile> (<cutoff>)`, then `**Lenses:** run: <list>; skipped: <list with reason>` (write `skipped: none` when every enabled lens ran); a counts table (P0, P1, P2, P3); `## Checks run` (Check, Result); `## Findings` (table with `# | ID | Severity | Confidence | Category | Location | Claim | Verdict`), then one `### <id>` block per finding with `- Evidence:` and `- Fix:`; `## Dropped` (ID, Claim, Verdict, Reason). With no findings or drops, write `None.` under that heading.

## 7. Fix briefs

Emit one fix brief per surviving finding for an `engineer` agent (used by [fix-loop.md](fix-loop.md)), after the report:

```
fix brief F-1:
  file: src/auth/login.py:42-47
  problem: <claim>
  evidence: <evidence>
  do: <suggested_fix>
  test: add or update a test that fails before the fix and passes after
  limits: touch only what the fix needs; no unrelated changes
```

In staged mode, fix briefs go to the user or engineer; the fix loop does not run.

## 8. Stamp (staged mode only)

Write the stamp only in staged mode. Never write it in a branch, PR or ticket review. The format is in `docs/review-stamp.md`.

1. At the start of the review, record the staged-diff hash: the first field of `git diff --cached | sha256sum`.
2. After the review finishes (report written), run `git diff --cached | sha256sum` again. If the hash differs from the one at the start, the staged diff changed mid-review: do not write a stamp, and tell the user the review is stale and must be re-run.
3. Get the stamp path with `git rev-parse --git-path neral/review-stamp.json` (do not hard-code `.git/neral/`: in a linked worktree `.git` is a file). Create its parent directory if it is missing, then write the stamp at that path with all 7 fields:

| Field | Value |
|---|---|
| `diff_sha256` | the hash from step 2 (64 lowercase hex characters, without the trailing ` -`) |
| `verdict` | the verdict from section 4: `PASS`, `PASS WITH NOTES` or `CHANGES NEEDED` |
| `worst_severity` | the worst surviving finding after the profile cutoff (`P0`-`P3`), or `null` if none survive |
| `profile` | the `precommit.profile` the review ran with |
| `lenses` | the list of lenses that ran |
| `reviewed_at` | when the review finished, UTC ISO 8601, e.g. `2026-11-09T14:03:22Z` |
| `neral_version` | `version` from `.claude-plugin/plugin.json` |

A failed pre-merge check must make the stamp invalid: when any check in section 2 fails, set `verdict` to `CHANGES NEEDED`, even if no finding survives.
