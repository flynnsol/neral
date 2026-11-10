# Step 3: Parallel lens passes

Run one `reviewer` per lens over the change, in parallel, then merge the results into one candidate findings list.

## Inputs

- The context pack from step 1 ([context-pack.md](context-pack.md)).
- The gate hints block from step 2 ([gate.md](gate.md)).
- The effective config (`.neral/config.yml` merged over the defaults in `docs/config-schema.md`).

## Which lenses run

The six lenses are `correctness`, `security`, `data-integrity`, `tests`, `performance`, `maintainability`.

1. If `lenses` is set in `.neral/config.yml`, that list is the enabled set. Otherwise all six are enabled.
2. Profile `quiet`: run only `correctness`, `security` and `data-integrity` (the enabled lenses among them).
3. Profile `standard` and `strict`: run every enabled lens.

In staged mode (see [SKILL.md](SKILL.md)), the enabled set comes from `precommit.lenses` and the profile from `precommit.profile`, not the top-level `lenses` and `profile` keys. Defaults: lenses `correctness`, `security`, `data-integrity`; profile `quiet`.

## Launch

Launch ONE `reviewer` subagent per lens, all in a SINGLE message with several Agent calls, so they run in parallel. Never launch them one after another.

Each brief contains:

- The lens name. The reviewer reads `lenses/<lens>.md` itself.
- The context pack and the gate hints.
- The `path_instructions` and approved learnings that match the changed paths.
- The instruction: return a JSON array of findings in the `docs/finding-schema.md` format, and nothing else (`[]` if none).

Never pass the author's reasoning, commit messages that describe intent beyond the ticket text, or chat history.

## Large diffs

If the pack is too big for one reviewer to read well (roughly over 1500 diff lines or 25 changed files), split the changed files into chunks, grouped by directory so related files stay together. Run each lens once per chunk, all in one parallel message. Each chunk brief carries that chunk's diff, plus the shared rules, hints and instructions.

## Merge and dedupe

1. Parse each reviewer's output as a JSON array. Discard unparsable output and re-run that lens (or chunk) once. If it fails again, record the lens as `failed` and continue.
2. Drop every finding with empty or missing evidence.
3. Drop findings whose `file` matches an `ignore` glob. Drop findings for files outside the change unless a changed file calls into them.
4. Key each finding by (`file`, overlapping line range, normalized claim). Two findings collide when they share a file, their line ranges overlap (a single line is a range of one), and their claims match after lowercasing and collapsing whitespace and punctuation, or clearly state the same defect.
5. On a collision keep one finding: the highest severity (P0 over P3) and the highest confidence. Keep the evidence and fix of the kept finding. Record every lens that raised it in a `lenses` field (for example `"lenses": ["correctness", "tests"]`).
6. Reassign ids sequentially as `F-1` to `F-n`, ordered by severity, then confidence.
7. Apply `path_instructions`: a finding that contradicts an instruction for its path is dropped.

Do not apply the profile severity cutoff here. Step 4 does that.

## Output

The merged candidate findings list: a JSON array in `docs/finding-schema.md` format (no `verdict`), each with its `lenses` field, plus a one-line note of lenses that ran and any that failed. Pass it to verification ([verify.md](verify.md)).
