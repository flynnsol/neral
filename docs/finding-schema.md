# Finding schema and report format

Shared contract for the reviewer, verifier, tester and the review pipeline. Agents emit and consume the records below exactly as written.

## Finding record

| Field | Type | Allowed values | Set by |
|---|---|---|---|
| `id` | string | Unique per review, `F-<n>` (e.g. `F-1`) | reviewer |
| `lens` | string | Name of the review lens that raised it (e.g. `security`, `concurrency`) | reviewer |
| `severity` | enum | `P0` critical: security exploit, data loss, severe crash. `P1` defect: wrong data, race, broken contract. `P2` quality: missing tests, dead code, naming. `P3` nit | reviewer |
| `category` | enum | `security`, `stability`, `data-integrity`, `correctness`, `performance`, `maintainability` (exactly these six) | reviewer |
| `confidence` | enum | `high`, `medium`, `low` | reviewer |
| `file` | string | Repo-relative path | reviewer |
| `line` | integer or string | Line number `42` or range `"42-58"` | reviewer |
| `claim` | string | One sentence stating the defect | reviewer |
| `evidence` | string | Code excerpt, command output or failing test | reviewer, tester |
| `suggested_fix` | string | Short fix brief an engineer agent can act on | reviewer |
| `verdict` | enum | `CONFIRMED`, `REFUTED`, `INCONCLUSIVE`. Absent before verification | verifier |

```json
{
  "id": "F-1",
  "lens": "security",
  "severity": "P0",
  "category": "security",
  "confidence": "high",
  "file": "src/auth/login.py",
  "line": "42-47",
  "claim": "The login query interpolates user input into SQL.",
  "evidence": "db.execute(f\"SELECT * FROM users WHERE name='{name}'\")",
  "suggested_fix": "Use a parameterised query and add a test with a quote in the name.",
  "verdict": "CONFIRMED"
}
```

Rules: REFUTED findings are dropped from the ranking and listed under "Dropped". INCONCLUSIVE findings stay ranked and are flagged.

## Report

| Element | Definition |
|---|---|
| Overall verdict | `PASS`, `PASS WITH NOTES` or `CHANGES NEEDED` (rule below) |
| Merge-risk score | Integer 0-5, **5 = safest to merge**, 0 = do not merge. Lower it for each P0/P1 and for failed checks |
| Counts | Number of surviving findings per severity (P0, P1, P2, P3) |
| Ranked findings | Sorted by severity (P0 first), then confidence (high first). Excludes REFUTED |
| Checks run | Ticket Acceptance, touches (changed files stay within the ticket's declared files), size limit. Each `pass` or `fail` |
| Profile used | `quiet`, `standard` or `strict` |
| Lenses | `run: <list>; skipped: <list with reason>`. Write `skipped: none` when every enabled lens ran |
| Dropped | REFUTED findings with the verifier's reason |

Verdict rule: `CHANGES NEEDED` if any P0 or P1 survives, or any check fails. `PASS WITH NOTES` if only P2/P3 findings survive. `PASS` if none survive and all checks pass.

### Profiles and severity cutoff

| Profile | Severities reported |
|---|---|
| `quiet` | P0-P1 |
| `standard` | P0-P2 |
| `strict` | P0-P3 (all) |

Findings below the profile cutoff are not listed; they are omitted from counts and ranking.

## Example report

```markdown
# Review: T12 Add login endpoint

**Verdict:** CHANGES NEEDED
**Merge-risk score:** 2/5 (5 = safest to merge)
**Profile:** standard (P0-P2)
**Lenses:** run: correctness, security, data-integrity, tests, performance, maintainability; skipped: none

| P0 | P1 | P2 | P3 |
|---|---|---|---|
| 1 | 0 | 1 | 0 |

## Checks run

| Check | Result |
|---|---|
| Ticket Acceptance | pass |
| Touches | fail: `src/db/pool.py` not declared |
| Size limit (200 lines, 5 files) | pass |

## Findings

| # | ID | Severity | Confidence | Category | Location | Claim | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | F-1 | P0 | high | security | `src/auth/login.py:42-47` | The login query interpolates user input into SQL. | CONFIRMED |
| 2 | F-3 | P2 | medium | maintainability | `src/auth/login.py:80` | `legacy_hash()` is never called. | CONFIRMED |

### F-1
- Evidence: `db.execute(f"SELECT * FROM users WHERE name='{name}'")`; test `name="a' OR '1'='1"` returns every user.
- Fix: Use a parameterised query and add a test with a quote in the name.

### F-3
- Evidence: `grep -rn legacy_hash src/` returns only the definition.
- Fix: Delete `legacy_hash()`.

## Dropped

| ID | Claim | Verdict | Reason |
|---|---|---|---|
| F-2 | Token expiry compares naive and aware datetimes. | REFUTED | Both values are converted to UTC at `login.py:61`; test passes. |
```
