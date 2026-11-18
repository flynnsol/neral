---
name: campaign
description: Plan a marketing or sales campaign for a product. Use when the user asks who to sell to, for pitches, for campaign copy or to plan a campaign. Runs the sales agent, then the marketing agent, and files the campaign only on the user's yes.
---

# campaign

Plan a campaign from a product. The agents report in the format of `docs/campaign-schema.md`.

## Rules

- Never file, publish or send anything without a yes.
- Run this skill in the main session, so you (not a subagent) launch both agents.

## Steps

1. **Gather the product** (repo path, README or description) and the goal.
2. **Run `sales`** (`agents/sales.md`) with the product and goal. It returns the audience brief.
3. **Show the audience brief** and let the user adjust `target_first`.
4. **Run `marketing` with the audience brief** (`agents/marketing.md`), as adjusted. It returns the campaign draft and an Ideas list.
5. **Show the campaign draft and its copy**, plus the Ideas list.
6. **File**: only on the user's explicit yes, file it with `engram:plan`. The draft epic becomes an epic and each ticket a ticket: `done_when` becomes its Acceptance, `owner` its role, `deliverable` goes into its body, and no `touches` (campaign tickets change no code). If Engram is not installed, save the draft as a Markdown file at a path the user names.

## References

- `docs/campaign-schema.md`: audience brief and campaign draft formats.
- `agents/sales.md` and `agents/marketing.md`: the two campaign agents.
