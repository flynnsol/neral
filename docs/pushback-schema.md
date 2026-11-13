# Pushback report schema

Shared contract for the `architect` and `product-manager` planning agents and the `neral:challenge` skill. Each agent reads a plan and returns one report in the format below. `neral:challenge` merges the reports and puts the questions to the user. Agents emit and consume the records below exactly as written.

## Report

| Field | Type | Allowed values | Set by |
|---|---|---|---|
| `agent` | enum | `architect` or `product-manager` | agent |
| `verdict` | enum | `challenges` (at least one challenge) or `no_concerns` (none) | agent |
| `challenges` | list | Challenge records (below). Empty list `[]` when `verdict` is `no_concerns` | agent |
| `assumptions` | list of strings | What the agent took as given while reading the plan. Required for both verdicts, including `no_concerns` | agent |

## Challenge record

| Field | Type | Allowed values | Set by |
|---|---|---|---|
| `id` | string | Unique per report, `C-<n>` (e.g. `C-1`) | agent |
| `severity` | enum | `blocker`: the plan cannot work or breaks a hard limit as written. `major`: likely rework, wrong scope or a missing decision. `minor`: worth a question, not worth stopping for | agent |
| `topic` | string | Short label (e.g. `data model`, `scope`, `user value`) | agent |
| `claim` | string | One sentence stating the concern | agent |
| `evidence` | string | A quote from the plan, a repo path and line (`src/db/pool.py:42`), or the limit that is breached | agent |
| `question` | string | The question to put to the user | agent |
| `suggestion` | string | Optional. One line. Never a rewritten plan | agent |

## Rules

- Challenge only when something warrants it. `no_concerns` is a valid and expected verdict; do not pad a report with invented challenges to look useful.
- Every challenge needs evidence. A challenge without `evidence` is dropped by `neral:challenge`.
- Agents never rewrite the plan. They raise questions; the user decides. A `suggestion` is one line at most.
- `assumptions` is always present, so the user can see what each agent took as given even when it raised nothing.
- `verdict` and `challenges` must agree: `challenges` needs a non-empty list, `no_concerns` needs `[]`.

## Example: `challenges`

```json
{
  "agent": "architect",
  "verdict": "challenges",
  "challenges": [
    {
      "id": "C-1",
      "severity": "blocker",
      "topic": "ticket size",
      "claim": "Ticket T3 rewrites the config loader and every caller in one change.",
      "evidence": "Plan, T3: \"Replace load_config() and update all 14 call sites.\" Breaches the 200-line, 5-file ticket limit.",
      "question": "Can T3 be split into a new loader first and caller migration after?",
      "suggestion": "Split T3 into a loader ticket and a migration ticket."
    },
    {
      "id": "C-2",
      "severity": "minor",
      "topic": "data model",
      "claim": "The plan adds a second timestamp format alongside the existing one.",
      "evidence": "src/neral/stamp.py:18 already writes ISO 8601 UTC; plan T5 says \"store epoch seconds\".",
      "question": "Should T5 reuse the existing ISO 8601 format?"
    }
  ],
  "assumptions": [
    "The ticket size limit is 200 changed lines and 5 files.",
    "No external consumer reads the stamp format."
  ]
}
```

## Example: `no_concerns`

```json
{
  "agent": "product-manager",
  "verdict": "no_concerns",
  "challenges": [],
  "assumptions": [
    "The only users are developers running neral locally.",
    "The plan's stated goal matches what the user asked for."
  ]
}
```

## How `neral:challenge` merges

Brief; the skill itself is a later ticket.

1. Drop any challenge without `evidence`.
2. Dedupe overlapping challenges (same concern from both agents): keep one, at the higher severity, and note both agents.
3. Rank `blocker`, then `major`, then `minor`.
4. Show every agent's `assumptions`, including those that returned `no_concerns`.
5. If no challenges survive, report that both agents found no concerns; do not invent questions.
