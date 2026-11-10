# Maintainability lens

Review the diff for things that will make the code harder to understand or change safely.

## Look for

- Dead code: unused functions, parameters, flags, imports of removed features, unreachable branches, commented-out blocks.
- Duplicated logic: copy-pasted blocks or a second implementation of something that already exists in the repo.
- Misleading names: a name, docstring or comment that says one thing while the code does another, especially after the diff changed behavior.
- Leaky or tangled structure: a layer reaching past its neighbor, circular dependencies, one function doing unrelated jobs, magic values repeated across files.
- Contract drift in docs: README, schema docs or comments that no longer match the changed code.
- Leftover debugging, TODOs without owner, and stale config keys.
- Overly clever code where a simple form exists and the cleverness hides a risk.

## How to check

- Grep for uses of anything the diff adds or orphans.
- Search the repo for existing helpers before accepting new ones.

## Ignore

- Formatting, import order, line length, quote style and anything a linter or formatter already enforces.
- Personal taste in naming or structure with no concrete confusion risk.
- Refactors of untouched code.

## Category

Emits `maintainability`, normally P2 (P3 for minor cases). If a misleading name or stale doc causes actual wrong behavior, report it as `correctness` instead.
