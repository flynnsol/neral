---
name: challenge
description: Challenge a draft plan, project, epic or feature before it is accepted. Use when the user asks to challenge, stress-test or sanity-check a plan before work starts. Launches the architect and product-manager agents in parallel, merges their evidenced challenges and puts them to the user as questions.
---

# challenge

Challenge a draft plan before it is accepted. The agents report in the format of `docs/pushback-schema.md`; this skill merges the reports and puts the questions to the user.

## Rules

- Run this skill in the main session. Subagents cannot spawn subagents, so the orchestrator (you) launches both agents itself.
- Pass the plan as text. Never pass a vault path to the agents, and never let them read the vault.
- Never invent challenges. Only challenges the agents raised, with evidence, reach the user.
- Never edit or rewrite the plan. The skill asks; the user decides.

## Steps

1. **Build the brief** from [brief.md](brief.md): plan text, repo path and optional project rules.
2. **Launch the agents.** Launch `architect` and `product-manager` in parallel: one message with two Agent calls, each given the same brief.
3. **Check each report** against `docs/pushback-schema.md`. If an agent returns malformed output (not valid JSON, missing fields, or a `verdict` that disagrees with `challenges`), say so, show it raw and continue with the other agent's report.
4. **Merge** the valid reports:
   - Drop every challenge without `evidence`.
   - Dedupe. Two challenges overlap when they cite the same plan ticket or section and concern the same decision or limit. When merged, keep the higher severity, name both agents, and keep both questions only if they differ.
   - Different concerns about the same ticket do not merge.
   - Rank `blocker`, then `major`, then `minor`.
   - Show every agent's `assumptions`, including from an agent that returned `no_concerns`.
5. **Ask the user**: present the ranked list as questions, each with its severity, agents, claim and evidence. Use AskUserQuestion where a challenge has clear choices. Relay the user's answers back as the outcome of the challenge, so the user (not the skill) updates the plan.
6. **No concerns**: if both agents return `no_concerns`, or no challenge survives the merge, say that the agents found no concerns and list their assumptions. Do not make up questions.

## References

- `docs/pushback-schema.md`: report and challenge record format, and the merge outline.
- `agents/architect.md` and `agents/product-manager.md`: the two planning agents.
