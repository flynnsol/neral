# Tests lens

Review the tests in and around the diff: do they actually protect the changed behavior?

## Look for

- Untested branches in the diff: new conditions, error paths, edge cases and config options with no test.
- Tests that cannot fail: no assertions, assertions on mocks of the code under test, `assert True`, expectations computed with the same logic as the code, exceptions caught and ignored.
- Tests that assert the wrong thing: expected values copied from buggy output, checking a side effect instead of the result, wrong field or unit.
- Flaky patterns: real clocks, sleeps, random data without a seed, network calls, shared global state, order dependence, uncleaned temp files or ports.
- Over-mocking that hides contract drift between layers: mocks that no longer match the real signature or response shape.
- Changed behavior with unchanged tests: old tests still passing because they never covered the change.
- Deleted or skipped tests with no stated reason.

## How to check

- For each new branch in the diff, name the test that would fail if it were removed.
- Mentally mutate the change (flip a condition) and see whether any test would notice.

## Ignore

- Coverage percentages and test style or naming preferences.
- Missing tests for trivial getters, pure config or generated code.
- Tests for code the diff does not touch.

## Category

Emits `maintainability` for missing or weak tests (typical severity P2). Emits `correctness` when a test asserts the wrong behavior, or cannot fail where it guards a real defect (P1 if it hides a live bug).
