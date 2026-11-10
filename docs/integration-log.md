# Integration log: v0.1.0 end-to-end run

Run on 2026-11-09 with Neral installed from this repo and the Engram vault driving the tickets. Two real tickets went through `neral:engineer`, then the `neral:review` pipeline: T33 (README install and marketplace description) and T34 (staged-mode notes). The pipeline was also pointed at the existing hook code (commit 7e861f2) to check that it finds real defects, not only empty results.

## What was run

| Step | Result |
|---|---|
| T33 and T34 built by `neral:engineer` in worktrees | Both committed once, tests green (34) |
| `neral:review` on T34, standard profile, six lenses | 6 of 6 lenses returned no findings; verdict PASS |
| `neral:review` on T33, quiet lenses (correctness, security) | 1 finding (P1, install command); the `verifier` REFUTED it with `claude plugin install --help` output; verdict PASS |
| `neral:review` on hook code 7e861f2, quiet lenses (correctness, security, data-integrity) | 8 raw findings, 5 after dedupe; 2 P1 confirmed by `verifier` and by `tester` repro tests |

## Findings on the hook code (commit 7e861f2)

| ID | Sev | Claim | Verdict |
|---|---|---|---|
| H1 | P1 | `parse_command` misses `git commit` in subshells, `if` blocks, `bash -c`, `env`, `command`, `sudo`, `time` | CONFIRMED, repro fails on 8 forms |
| H2 | P1 | `git commit -a` and `git commit <paths>` bypass the gate; an empty index counts as "nothing staged" | CONFIRMED, repro fails |
| H3 | P2 | `git -C <dir>` and `cd` targets are ignored, so the wrong repo is checked | Below the quiet cutoff, not verified |
| H4 | P3 | A stamp missing `verdict` or `worst_severity` is accepted | Below the cutoff, not verified |
| H5 | P3 | `block_on: P3` is accepted though the schema allows only P0 to P2 | Below the cutoff, not verified |

The verifier noted that H1 is a guardrail gap, not a sandbox escape: the gate protects against Claude's own accidental commits, so P2 is arguable. It is kept at P1 because the fix is cheap.

## Gaps found and what to do

| # | Gap | Action |
|---|---|---|
| 1 | Hook bypasses H1 to H5 (above) | Fix in T35 and T36 |
| 2 | `engram:work` reviews with a single `reviewer` agent, not the `neral:review` pipeline | Add a rule so Claude runs `neral:review` after a ticket reaches review (T23) |
| 3 | Six lens passes on a 3-line docs diff is wasteful | Scale lenses to the diff: docs-only changes run `correctness` only (T23) |
| 4 | Reviewers lack environment facts (the install-flag false positive) | Include `claude plugin validate` output and CLI help checks in gate hints (T23) |
| 5 | Worktree agents hit refusals on chained git commands and inline scripts that mention git | Tell `engineer` to run git as plain separate commands (T23) |
| 6 | One agent stalled when a trim edit was refused and left uncommitted work | Orchestrator finishes the commit; keep tickets under the size limit |
| 7 | Agents use an Opus co-author trailer when the brief asks for Sonnet | Decide on one attribution rule; not a plugin defect |
| 8 | The learnings flow was not exercised | Cover it in a later run |
