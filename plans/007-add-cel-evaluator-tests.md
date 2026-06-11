# Plan 007: Add unit tests for CEL evaluator

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/utils/cel_evaluator.py`
> If it changed, read the current version before writing tests.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: tests
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

`server/utils/cel_evaluator.py` (371 lines) implements the event-hints rules
engine — user-configured CEL expressions that auto-fill event names and categories.
It has two evaluation modes (single-item vs aggregate), security limits
(MAX_EXPRESSION_LENGTH, MAX_NESTING_DEPTH, EVALUATION_TIMEOUT_SECONDS), and custom
aggregate functions (sum, count, avg, min_val, max_val, all_match, any_match).
There are zero direct unit tests for this module. A regression in expression parsing,
type coercion, or the aggregate functions would silently break hint evaluation.

## Current state

`server/utils/cel_evaluator.py` — CEL evaluator. Key public API:

```python
# Main evaluation function (guessed from the module structure — verify by reading):
evaluate_cel_expression(expression: str, line_items: list[dict]) -> bool
```

The module exposes (read the file to confirm exact function names and signatures):
- A function that validates an expression (raises `CELValidationError` on invalid input)
- A function that evaluates an expression against a list of line item dicts
- `CELValidationError` exception class

A line item dict for evaluation has keys: `description`, `amount`,
`payment_method`, `responsible_party`.

`server/tests/test_event_hints.py` — existing API-level tests for event hints.
Use this file as the structural pattern (class structure, fixture usage).

## Commands you will need

| Purpose   | Command                                                          | Expected on success |
|-----------|------------------------------------------------------------------|---------------------|
| New tests | `cd server && uv run python -m pytest tests/test_cel_evaluator.py -v` | all pass |
| All tests | `cd server && uv run python -m pytest -v`                        | all pass |
| Lint      | `cd server && make lint`                                         | exit 0 |

## Scope

**In scope**:
- `server/tests/test_cel_evaluator.py` (new file to create)

**Out of scope**:
- `server/utils/cel_evaluator.py` — read only.
- Any existing test file.

## Git workflow

- Branch: `advisor/007-add-cel-evaluator-tests`
- Commit message style: `Add unit tests for CEL evaluator (#NNN)`

## Steps

### Step 1: Read `cel_evaluator.py` in full

Read `server/utils/cel_evaluator.py` completely before writing any tests. Identify:
- The exact names and signatures of the public functions (evaluate, validate, etc.)
- What input types they accept
- What exceptions they raise
- How single-item vs aggregate expressions differ
- The `CELValidationError` exception class

### Step 2: Create `server/tests/test_cel_evaluator.py`

No database or Flask app context is needed — the CEL evaluator is a pure
Python function. Import directly:

```python
from utils.cel_evaluator import CELValidationError
# and whatever the main evaluate/validate functions are named
```

**Test cases to implement** (adapt function names to match what you found in step 1):

**Single-item expression tests**:
- `test_description_contains_match`: expression `description.contains("spotify")`,
  item with `description="Spotify Premium"` → True
- `test_description_contains_no_match`: same expression, item `description="Netflix"` → False
- `test_amount_comparison`: expression `amount > 50.0`, item `amount=100.0` → True
- `test_payment_method_match`: expression `payment_method == "venmo"`,
  item `payment_method="Venmo"` (note: strings are lowercased internally) → True
- `test_multiple_line_items_any_match`: multiple items, at least one matches → True

**Aggregate expression tests**:
- `test_sum_expression`: expression `sum(amount) > 200`,
  items `[{amount: 100}, {amount: 150}]` → True
- `test_count_expression`: expression `count() == 2`,
  two items → True

**Validation tests**:
- `test_expression_too_long`: expression of length > 500 characters →
  raises `CELValidationError`
- `test_invalid_expression_syntax`: expression `this is not valid CEL` →
  raises `CELValidationError`

**Verify**: `cd server && uv run python -m pytest tests/test_cel_evaluator.py -v` → at least 9 tests pass.

### Step 3: Run all tests

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

### Step 4: Lint

**Verify**: `cd server && make lint` → exit 0.

## Done criteria

- [ ] `server/tests/test_cel_evaluator.py` exists with at least 9 test functions
- [ ] All 9 tests pass
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] Only `server/tests/test_cel_evaluator.py` created
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- The CEL evaluator's public functions have different names or signatures than
  expected — adapt the tests to match what is actually in the file.
- The evaluator requires a Flask app context (it shouldn't, but verify). If it does,
  add the `flask_app` fixture from conftest.

## Maintenance notes

- If the CEL evaluator gains new aggregate functions, add corresponding tests.
- The `EVALUATION_TIMEOUT_SECONDS = 2.0` limit and `MAX_NESTING_DEPTH = 10` are
  security controls; add edge-case tests for those if expression injection is a concern.
