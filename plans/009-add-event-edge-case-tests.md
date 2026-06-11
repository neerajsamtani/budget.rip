# Plan 009: Add tests for event creation edge cases

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/resources/event.py server/tests/test_event.py`
> If either changed, compare before proceeding.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: 002 (the guard must exist before testing it)
- **Category**: tests
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

Plan 002 adds a guard that returns 400 when all provided line item IDs are invalid.
That guard has no test coverage until this plan. Additionally, the event creation
path silently produces different results depending on whether line items exist —
documenting these behaviors in tests makes future refactors safe.

## Current state

`server/tests/test_event.py` — existing event tests. See `TestEventAPI` class
starting at line 43. Uses fixtures: `test_client`, `jwt_token`, `flask_app`,
`create_line_item_via_manual`, `create_event_via_api`.

`server/tests/conftest.py` — fixture definitions.

## Commands you will need

| Purpose   | Command                                                    | Expected on success |
|-----------|------------------------------------------------------------|--------------------|
| Tests     | `cd server && uv run python -m pytest tests/test_event.py -v` | all pass |
| All tests | `cd server && uv run python -m pytest -v`                  | all pass |
| Lint      | `cd server && make lint`                                   | exit 0 |

## Scope

**In scope**:
- `server/tests/test_event.py`

**Out of scope**:
- `server/resources/event.py` — if plan 002 is not done yet, do plan 002 first.

## Git workflow

- Branch: `advisor/009-add-event-edge-case-tests`
- Commit message style: `Add tests for event creation with invalid line item IDs (#NNN)`

## Steps

### Step 1: Read the existing test file

Read `server/tests/test_event.py` in full to understand the fixture usage and
class structure.

### Step 2: Add two new test cases to `TestEventAPI`

**Test 1 — create event with nonexistent line item IDs returns 400**:
```python
def test_event_creation_with_nonexistent_line_item_ids_returns_400(
    self, test_client, jwt_token
):
    """Event creation with IDs that don't exist returns 400, not 500"""
    response = test_client.post(
        "/api/events",
        json={
            "name": "Test Event",
            "category": "Food",    # use any valid category name in your test DB
            "line_items": ["li_does_not_exist_1", "li_does_not_exist_2"],
            "tags": [],
        },
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
```

**Test 2 — update event with nonexistent line item IDs returns 400**:
Create a real event first (using `create_line_item_via_manual` + `create_event_via_api`),
then send a PUT to `/api/events/<id>` with nonexistent line item IDs.
Assert 400.

**Verify**: `cd server && uv run python -m pytest tests/test_event.py -v -k "nonexistent"` → 2 tests pass.

### Step 3: Run all tests

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

### Step 4: Lint

**Verify**: `cd server && make lint` → exit 0.

## Done criteria

- [ ] 2 new tests in `test_event.py` — both pass
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] Only `server/tests/test_event.py` modified
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- Plan 002 was not executed: the endpoint still returns 500 instead of 400 for
  nonexistent IDs. Execute plan 002 first, then return here.

## Maintenance notes

- If the category fixture in conftest changes, update the `"category"` value in
  test 1 accordingly.
