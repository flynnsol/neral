# Step 6: Learnings proposals

Turn review outcomes into durable, human-approved repo rules stored in `.neral/learnings.md`. Entry format and precedence are defined in `docs/config-schema.md`.

## 1. When to propose

Propose a learning only when one of these holds:

- The user dismisses a finding as a false positive, or says to stop flagging something.
- The same kind of finding was raised and fixed the same way on 3 or more reviews.
- The user states a standing preference during review.

Never propose from a single unverified opinion of an agent. Every proposal needs a user statement or repeated confirmed findings behind it.

## 2. Where proposals live

- Write pending proposals to `.neral/proposed.md`, a separate file, in the same entry format, each with `status: proposed`.
- `.neral/learnings.md` holds only approved entries. Never write a `proposed` or `rejected` entry there.
- Create `.neral/proposed.md` if it is missing. Delete it when it has no entries left.

## 3. Entry format

One top-level bullet per entry, indented fields:

```markdown
- Prefer early returns over nested conditionals in request handlers.
  - path: `src/api/**`
  - date: 2026-11-09
  - source: F-3
  - status: proposed
```

- Rule: one plain-language sentence, no finding-specific details.
- `path`: optional glob; omit for a repo-wide rule. Keep it as narrow as the evidence supports.
- `date`: today, `YYYY-MM-DD`.
- `source`: id of the finding that prompted the rule.
- `status`: `proposed` in `proposed.md`, `approved` in `learnings.md`.

## 4. Dedupe and precedence

Before proposing, check existing `.neral/learnings.md` entries and config `path_instructions`.

- Skip a rule that an existing entry or `path_instructions` item already covers.
- `config.yml` wins over `learnings.md`. If a proposal conflicts with the config, do not propose it; tell the user the config must change instead.

## 5. Approval flow

For each entry in `.neral/proposed.md`:

1. Show it as a diff of `.neral/learnings.md` (the entry as an added `+` block with `status: approved`).
2. Ask the user to approve, edit or reject.
3. Approve: move the entry from `proposed.md` into `learnings.md` with `status: approved`.
4. Edit: apply the user's wording, show the diff again, then ask again.
5. Reject: remove the entry from `proposed.md` and record nothing. `rejected` is never written to `learnings.md`.

Never write to `.neral/learnings.md` without explicit approval. Entries produced by this approval flow are the only way learnings are written; no other step, agent or fix loop may add or change them.

## 6. Keep it short

When touching `learnings.md`, suggest pruning entries whose `path` glob matches no files anymore. Remove an entry only after the user agrees.
