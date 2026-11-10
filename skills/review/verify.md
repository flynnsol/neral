# Step 4a: Verify findings

Try to refute every candidate finding before it is ranked. No evidence, no finding.

## Inputs

- The merged candidate findings list from step 3 ([passes.md](passes.md)).
- The context pack from step 1 ([context-pack.md](context-pack.md)).

## Verifier launch

1. Launch ONE `verifier` subagent per finding, all in a SINGLE message with several Agent calls, so they run in parallel. If there are many findings (over about 15), batch them in several messages, each batch fully parallel.
2. Each brief holds exactly ONE finding record (without `verdict`) and the diff and context pack. Never pass the other findings, the reviewer's reasoning or the author's reasoning.
3. Parse each reply as the finding with `verdict` and `verifier_notes`. If a reply is unparsable or has no evidence in `verifier_notes`, re-run that verifier once; if it fails again, treat the verdict as `INCONCLUSIVE`.

## Repro with the tester

Launch a `tester` (repro job) for a finding when:

- its severity is `P0` or `P1`, or
- its verifier recommends a repro in `verifier_notes`.

Launch all testers for a round in a SINGLE message. Brief each with one finding and the test command from the config or repo. The tester writes a failing repro test and runs it:

- The test fails as the finding claims: verdict `CONFIRMED`, with the test path and failing output added to `evidence`.
- The test passes: verdict `REFUTED`, with the passing output as the reason.
- The tester cannot reproduce cleanly: keep the verifier's verdict, and note why.

The tester's verdict overrides the verifier's. Tester files stay in the working tree only as evidence. Never commit them. Report the file path in the finding's evidence, or delete the file once the evidence is captured.

## Apply verdicts

| Verdict | Action |
|---|---|
| `CONFIRMED` | Keep the finding unchanged. |
| `INCONCLUSIVE` | Keep it. Lower `confidence` one level (`high` to `medium`, `medium` to `low`, `low` stays) and flag it as unverified, with what is missing. |
| `REFUTED` | Drop it. List it under Dropped with the id, claim, verdict and the verifier's or tester's reason. |

Drop any finding that still has empty evidence after verification.

## Output

The verified findings list: surviving findings in `docs/finding-schema.md` format, each with `verdict`, updated `confidence` and `evidence`, plus the Dropped list and the paths of any tester files left in the working tree. Pass it to the report ([report.md](report.md)).
