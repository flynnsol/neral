# Example ticket brief

A worked example of what an orchestrator hands the `engineer` subagent, and the report it returns. The ticket is made up.

## The brief

**Ticket:** T-12 Add a slugify helper to the utils module

**Text:** Add `slugify(text: str) -> str` to `src/utils.py`. It lowercases the text, replaces each run of non-alphanumeric characters with a single `-`, and strips leading and trailing `-`. Example: `slugify("Hello, World!")` returns `"hello-world"`.

```yaml
role: engineer
touches:
  - src/utils.py
  - tests/test_utils.py
```

**Acceptance checks**

```bash
python -m pytest tests/test_utils.py -q
python -c "from src.utils import slugify; assert slugify('Hello, World!') == 'hello-world'"
```

**Rules**

- Stay inside `touches`. Do not edit any other file.
- Test-first: write the failing test, see it fail, then implement.
- One commit, under 200 lines changed and 5 files.
- No vault access.
- Do not merge or push.
- If the scope widens, stop and report instead of continuing.

## The report

```markdown
### What changed
Added `slugify` to `src/utils.py` and four tests covering basic text,
repeated punctuation, leading/trailing separators, and empty input.

### Files
- src/utils.py (+9)
- tests/test_utils.py (+21)

### Commands run
- `python -m pytest tests/test_utils.py -q` (before the change): 4 failed, ImportError
- `python -m pytest tests/test_utils.py -q` (after): 4 passed
- `python -c "from src.utils import slugify; ..."`: exit 0

### Concerns
Non-ASCII letters are treated as separators (`"Café"` gives `"caf"`).
The ticket did not cover this, so it is left as is. Suggest a follow-up ticket.

### Commit
`a1b2c3d` on branch `t-12-slugify`, not pushed.
```
