# Campaign schema

Shared contract for the `sales` and `marketing` agents and the `neral:campaign` skill. `sales` returns an audience brief. `marketing` reads it and returns a campaign draft: an epic with tickets in Engram's ticket shape, so `engram:plan` can file it. Agents emit and consume the records below exactly as written.

## Audience brief (from `sales`)

| Field | Type | Contents |
|---|---|---|
| `product` | string | One or two sentences: what it is and who it is for |
| `segments` | list | Segment records (below) |
| `pitch_angles` | list of strings | One line each |
| `objections` | list | `{ "objection": string, "answer": string }` |
| `sales_campaigns` | list of strings | Direct sales pushes, one line each |
| `target_first` | list of strings | Segment `name`s marketing should target first, in order |

Segment record: `name`, `who`, `pain`, `why_now`, `where` (list of places to reach them). All strings except `where`.

## Campaign draft (from `marketing`)

The epic:

| Field | Type | Contents |
|---|---|---|
| `title` | string | Short campaign name |
| `goal` | string | One measurable outcome |
| `audience` | list of strings | Segment `name`s from the brief |
| `channels` | list of strings | e.g. `email`, `LinkedIn`, `blog` |
| `done_when` | string | Checkable condition for the whole campaign |
| `dates` | object | `{ "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" }` |
| `tickets` | list | Ticket records (below) |

Ticket record:

| Field | Type | Contents |
|---|---|---|
| `title` | string | Imperative, short |
| `what` | string | One or two sentences |
| `deliverable` | string | The copy itself, or a description of the asset |
| `channel` | string | One of the epic's `channels` |
| `owner` | string | A role, not a person (e.g. `copywriter`, `designer`) |
| `done_when` | string | Checkable: someone can say yes or no without judgement |

## Rules

- `target_first` and `audience` name segments that exist in the brief.
- Every ticket has a checkable `done_when`. "Looks good" is not checkable; "Published on the blog and linked from the newsletter" is.
- One deliverable per ticket.

## Example: audience brief

```json
{
  "product": "Neral, a Claude Code plugin that plans and builds tickets for small dev teams.",
  "segments": [
    {
      "name": "solo-founders",
      "who": "Technical founders shipping alone",
      "pain": "Planning and building compete for the same hours",
      "why_now": "Agent tooling is now good enough to hand off whole tickets",
      "where": ["Indie Hackers", "X"]
    }
  ],
  "pitch_angles": ["Plan once, ship tickets while you sleep"],
  "objections": [
    { "objection": "I don't trust agents with my code.", "answer": "Every ticket is one reviewed commit; nothing merges without you." }
  ],
  "sales_campaigns": ["Offer a 30-minute setup call to the first 20 founders"],
  "target_first": ["solo-founders"]
}
```

## Example: campaign draft

```json
{
  "title": "Solo founder launch",
  "goal": "100 installs from solo founders",
  "audience": ["solo-founders"],
  "channels": ["blog", "X"],
  "done_when": "100 installs tagged solo-founders by the end date",
  "dates": { "start": "2026-12-01", "end": "2026-12-31" },
  "tickets": [
    {
      "title": "Write the launch post",
      "what": "A blog post showing one ticket going from plan to commit.",
      "deliverable": "Headline: \"I shipped a week of tickets without writing them.\" 800 words, one screenshot.",
      "channel": "blog",
      "owner": "copywriter",
      "done_when": "Post is live on the blog with a working install link"
    }
  ]
}
```
