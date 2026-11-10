# Performance lens

Review the diff for changes that make the system noticeably slower or hungrier at realistic scale.

## Look for

- N+1 patterns: a query, API call or file read inside a loop over results; missing batching or eager loading.
- Unbounded work: loops, recursion, retries or polling with no limit; reading whole files or result sets into memory; unbounded caches or queues; missing pagination.
- Hot-path regressions: new work added to per-request, per-event or per-row code, repeated parsing or compilation, repeated serialization, synchronous I/O in async code.
- Algorithmic cost: quadratic scans over lists where a set or map fits, repeated sorting, string concatenation in loops.
- Missing indexes for new query filters or joins, and queries that defeat existing indexes.
- Cross-file effects: a helper that became expensive while its callers invoke it in a loop.
- Leaks that grow over time: listeners, timers, connections or handles never released.

## How to check

- Estimate the input size from context (rows, users, files) before calling something slow.
- Find the callers of any changed helper to see how often it runs.

## Ignore

- Micro-optimizations and cold paths (startup, admin scripts, one-off jobs).
- Speculative speedups with no measurable gain.
- Style choices that are equivalent in cost.

## Category

Emits `performance`. Emits `stability` instead only if the problem is an outage-class failure such as memory exhaustion or a hang. Typical severity: P1 for clear scaling regressions on hot paths, P2 otherwise. Lower confidence when the data size is a guess.
