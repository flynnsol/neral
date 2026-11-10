# Neral config and learnings schema

Neral reads these files from the `.neral/` directory at the repo root.

| File | Author | Purpose |
|------|--------|---------|
| `.neral/config.yml` | Human | Review settings. Template: `templates/config.yml` |
| `.neral/learnings.md` | Neral, after human approval | Approved review rules learned from past findings. Holds only `approved` entries |
| `.neral/proposed.md` | Neral | Pending proposals awaiting human review. Never applied |

## Rules

| Rule | Statement |
|------|-----------|
| Precedence | `config.yml` over `learnings.md`. On conflict, the config wins. |
| Missing directory | If `.neral/` is missing, all defaults apply. |
| Missing file or key | Each missing file or key falls back to its default. |
| Approval | `learnings.md` holds only `approved` entries, written after human approval. Pending proposals live in `proposed.md` and are never applied by the pipeline. |

## `.neral/config.yml`

YAML. All keys are optional.

| Key | Type | Allowed values | Default |
|-----|------|----------------|---------|
| `profile` | string | `quiet`, `standard`, `strict` | `standard` |
| `path_instructions` | list of objects | see below | `[]` |
| `custom_checks` | list of objects | see below | `[]` |
| `ignore` | list of strings | glob patterns | lock files, generated code, minified bundles |
| `test_command` | string | any shell command | unset |
| `lenses` | list of strings | `correctness`, `security`, `data-integrity`, `tests`, `performance`, `maintainability` | all six |
| `fix_loop.max_rounds` | integer | `>= 1` | `3` |

### `path_instructions` entry

| Key | Type | Allowed values | Default |
|-----|------|----------------|---------|
| `path` | string | glob | required |
| `instructions` | string | plain-language text | required |

### `custom_checks` entry

| Key | Type | Allowed values | Default |
|-----|------|----------------|---------|
| `name` | string | unique short identifier | required |
| `instructions` | string | plain-language pass/fail check | required |

### Default `ignore`

| Category | Globs |
|----------|-------|
| Lock files | `**/package-lock.json`, `**/yarn.lock`, `**/pnpm-lock.yaml`, `**/poetry.lock`, `**/Cargo.lock`, `**/go.sum` |
| Generated code | `**/*.generated.*`, `**/generated/**` |
| Minified bundles | `**/*.min.js`, `**/*.min.css`, `**/*.map` |

Setting `ignore` replaces this list; it does not extend it.

### Example

```yaml
profile: strict
path_instructions:
  - path: "src/api/**"
    instructions: "Handlers must validate input."
custom_checks:
  - name: no-todo-comments
    instructions: "Fail if the change adds a TODO without a ticket id."
test_command: "npm test"
lenses: [correctness, security]
fix_loop:
  max_rounds: 2
```

## `.neral/learnings.md`

A markdown list. Each entry is one top-level bullet with indented fields.

| Field | Type | Allowed values | Default |
|-------|------|----------------|---------|
| `rule` | string | plain-language rule (the bullet text) | required |
| `path` | string | glob | optional; omitted means repo-wide |
| `date` | string | `YYYY-MM-DD` | required |
| `source` | string | id of the finding that prompted it | required |
| `status` | string | `approved` | required |

| Status | File | Meaning |
|--------|------|---------|
| `approved` | `learnings.md` | Human approved. Applied to reviews. |
| `proposed` | `proposed.md` | Held pending human review. Never applied. |

`learnings.md` stores only `approved` entries. Rejected proposals are deleted, not stored.

```markdown
- Prefer early returns over nested conditionals in request handlers.
  - path: `src/api/**`
  - date: 2026-11-09
  - source: F-0042
  - status: approved
```

## `.neral/proposed.md`

Pending proposals. Same entry format as `learnings.md`, but each entry has `status: proposed`. The pipeline never applies these entries.

| Event | Result |
|-------|--------|
| Human approves | The entry moves to `.neral/learnings.md` with `status: approved`. |
| Human rejects | The entry is deleted. |

```markdown
- Prefer early returns over nested conditionals in request handlers.
  - path: `src/api/**`
  - date: 2026-11-09
  - source: F-0042
  - status: proposed
```
