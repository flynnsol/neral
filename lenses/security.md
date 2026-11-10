# Security lens

Review the diff for ways an attacker or untrusted input can cause harm.

## Look for

- Injection: SQL, shell commands, template, path traversal, header or log injection, unsafe deserialization, `eval`.
- Authentication and authorization gaps: new endpoints or handlers without auth checks, missing ownership checks (IDOR), checks done client-side only, role checks that can be bypassed.
- Secrets: keys, tokens or passwords committed, logged, returned in responses or put in URLs.
- Unsafe input handling: unvalidated or unbounded user input reaching files, queries, redirects, URLs (SSRF) or HTML (XSS).
- Weak crypto: homemade schemes, weak hashes for passwords, predictable tokens, disabled TLS verification.
- Cross-file trust: a helper that used to sanitize now bypassed, a validation layer removed, or a changed default (CORS, cookie flags, permissions) that widens access.
- New dependencies or permissions that expand the attack surface without need.

## How to check

- Trace each untrusted value from entry point to sink across files.
- Confirm that every new route, command or job enforces the same checks as its neighbors.

## Ignore

- Theoretical issues with no reachable path from untrusted input.
- Internal-only scripts and test fixtures with obviously fake credentials.
- Generic hardening advice not tied to a line in the diff.

## Category

Emits `security`. Typical severity: P0 for exploitable injection, auth bypass or leaked live secrets; P1 for exploitable-with-conditions issues. Use high confidence only when you can name the input and the sink.
