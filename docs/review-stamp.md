# Review stamp

The review stamp records that the exact staged diff was reviewed. The pre-commit gate reads it to decide whether a commit may proceed. Settings come from the `precommit` block in `.neral/config.yml` (see `docs/config-schema.md`).

## Location

`.git/neral/review-stamp.json`

The stamp lives inside `.git`, so it is never committed.

## Fields

| Field | Type | Allowed values | Meaning |
|-------|------|----------------|---------|
| `diff_sha256` | string | 64 lowercase hex characters | sha256 of the exact bytes of `git diff --cached` |
| `verdict` | string | `PASS`, `PASS WITH NOTES`, `CHANGES NEEDED` | Review verdict |
| `worst_severity` | string or null | `P0`, `P1`, `P2`, `P3`, `null` | Worst surviving finding; `null` when none survive |
| `profile` | string | `quiet`, `standard`, `strict` | Profile the review ran with |
| `lenses` | list of strings | lens names | Lenses the review ran |
| `reviewed_at` | string | ISO 8601 UTC, e.g. `2026-11-09T14:03:22Z` | When the review finished |
| `neral_version` | string | plugin version | Neral version that wrote the stamp |

## Hash command

```sh
git diff --cached | sha256sum
```

`diff_sha256` is the first field of this output (the hex digest only, without the trailing ` -`).

## Validity rule

A stamp is valid for a commit when all of these hold:

1. `diff_sha256` equals the hash of the current staged diff.
2. `worst_severity` is not at or above `precommit.block_on` (`null` always passes).
3. No check failed.

Severity order is P0 (worst), P1, P2, P3. With `block_on: P1`, a stamp with `worst_severity` `P0` or `P1` is invalid; `P2`, `P3` or `null` is valid. Any change to the staged diff after review invalidates the stamp. If the stamp is missing or invalid, the commit is denied.

## Example

```json
{
  "diff_sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
  "verdict": "PASS WITH NOTES",
  "worst_severity": "P2",
  "profile": "quiet",
  "lenses": ["correctness", "security", "data-integrity"],
  "reviewed_at": "2026-11-09T14:03:22Z",
  "neral_version": "0.1.0"
}
```

## Bypasses

The gate allows the commit without checking the stamp when any of these hold:

| Bypass | Condition |
|--------|-----------|
| Agent worktree | The current working directory is inside `.claude/worktrees/` |
| Environment | `NERAL_REVIEW=off` is set |
| Config | `precommit.enabled: false` in `.neral/config.yml` |
| Nothing staged | `git diff --cached` is empty |
| Hook error | Any error in the hook fails open: the commit is allowed |
