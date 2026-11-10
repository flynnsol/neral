# Correctness lens

Review the diff for code that does not do what its author intended or what its callers expect.

## Look for

- Logic errors: inverted conditions, off-by-one, wrong operator, wrong variable, unreachable branches.
- Unhandled edge cases: empty input, null/None, zero, negative values, unicode, time zones.
- Error handling: swallowed exceptions, ignored return values, missing cleanup on failure paths.
- Concurrency: races, check-then-act, shared mutable state, missing awaits.
- Cross-file breakage: callers not updated after a changed signature, renamed or removed symbol, or reordered arguments.
- Changed defaults: a new default value that silently alters behavior for existing callers or configs.
- Contract drift between layers: API handler, service and client disagreeing on field names, types, status codes or error shapes.
- Resource leaks that can crash the process: unclosed files or connections, unbounded retries, infinite loops.

## How to check

- Grep for every caller of each changed function, class or config key and confirm it still fits.
- Read the code on both sides of a boundary, not only the changed side.

## Ignore

- Style, naming and formatting (linters and the maintainability lens own these).
- Hypothetical bugs that need inputs the callers can never produce.
- Pre-existing issues in lines the diff does not touch, unless the diff makes them reachable.

## Category

Normally emits `correctness`. Emits `stability` when the defect is a crash, hang, leak or race rather than wrong output. Typical severity: P1 for wrong results or broken contracts, P0 for severe crashes.
