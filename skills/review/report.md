# Step 4b: Score and report

Turn the verified findings into the final review report. The format is the example in `docs/finding-schema.md`; reproduce its shape exactly.

## Inputs

- The verified findings list and Dropped list from [verify.md](verify.md).
- The effective config (`profile`, `custom_checks`) and the ticket, if any.

## 1. Severity cutoff

Read `profile` from config (default `standard`). Keep only findings at or above the cutoff:

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

Use this shape: an H1 `# Review: <ticket id and title, or branch>`; the lines `**Verdict:**`, `**Merge-risk score:** N/5 (5 = safest to merge)` and `**Profile:** <profile> (<cutoff>)`; a counts table (P0, P1, P2, P3); `## Checks run` (Check, Result); `## Findings` (table with `# | ID | Severity | Confidence | Category | Location | Claim | Verdict`), then one `### <id>` block per finding with `- Evidence:` and `- Fix:`; `## Dropped` (ID, Claim, Verdict, Reason). With no findings or drops, write `None.` under that heading.

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
