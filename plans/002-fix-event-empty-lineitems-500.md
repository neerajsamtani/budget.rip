# Plan 002: Guard event create/update against invalid line item IDs

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/resources/event.py`
> If `event.py` changed, compare the "Current state" excerpts before proceeding.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

The event creation endpoint validates that the request body includes at least one
line item ID, but it does not validate that those IDs actually exist in the database.
`get_line_item_amounts()` silently drops IDs that don't exist, returning an empty
list. The subsequent `min(line_items, ...)` call on an empty sequence raises an
unhandled `ValueError`, causing a 500 response. The same problem exists in the
update path. The client gets a 500 instead of a clear 400 with a message.

## Current state

`server/resources/event.py` — event CRUD endpoints.

**Create path** (`server/resources/event.py:70-86`):
```python
if len(new_event["line_items"]) == 0:           # checks request body count ✓
    ...
    return jsonify(...), 400

line_items = get_line_item_amounts(new_event["line_items"])   # may return [] if IDs invalid
earliest_line_item = min(line_items, key=lambda line_item: line_item["date"])  # ValueError if [] ←
```

**Update path** (`server/resources/event.py:113-119`):
```python
if "line_items" not in update_data or len(update_data["line_items"]) == 0:
    ...
    return jsonify({"error": "Event must have at least one line item"}), 400

filters: Dict[str, Any] = {"id": {"$in": update_data["line_items"]}}
line_items = get_all_line_items(filters)         # may return [] if IDs invalid
earliest_line_item = min(line_items, key=lambda li: li["date"])  # ValueError if [] ←
```

**`get_line_item_amounts`** (`server/dao.py:178-189`): queries by `LineItem.id.in_([...])` and returns only
rows that match — if no IDs exist, returns `[]`.

## Commands you will need

| Purpose   | Command                             | Expected on success |
|-----------|-------------------------------------|---------------------|
| Tests     | `cd server && uv run python -m pytest tests/test_event.py -v` | all pass |
| All tests | `cd server && uv run python -m pytest -v` | all pass |
| Lint      | `cd server && make lint`            | exit 0 |

## Scope

**In scope**:
- `server/resources/event.py` (two guard insertions)

**Out of scope**:
- `server/dao.py` — no changes to `get_line_item_amounts` or `get_all_line_items`.

## Git workflow

- Branch: `advisor/002-fix-event-empty-lineitems-500`
- Commit message style: `Return 400 when event line items resolve to empty (#NNN)`

## Steps

### Step 1: Add guard after create-path fetch

In `server/resources/event.py`, after line 74 (the `get_line_item_amounts` call),
insert a guard:

```python
line_items: List[Dict[str, Any]] = get_line_item_amounts(new_event["line_items"])
if not line_items:
    logger.warning("Event creation attempt: no valid line items found for provided IDs")
    return jsonify({"error": "None of the provided line item IDs exist"}), 400
earliest_line_item: Dict[str, Any] = min(line_items, key=lambda line_item: line_item["date"])
```

**Verify**: `grep -n "None of the provided line item IDs exist" server/resources/event.py` → 1 match.

### Step 2: Add guard after update-path fetch

In `server/resources/event.py`, after the `get_all_line_items(filters)` call (around line 118),
insert the same guard:

```python
line_items: List[Dict[str, Any]] = get_all_line_items(filters)
if not line_items:
    logger.warning(f"Event update attempt for {event_id}: no valid line items found for provided IDs")
    return jsonify({"error": "None of the provided line item IDs exist"}), 400
earliest_line_item: Dict[str, Any] = min(line_items, key=lambda li: li["date"])
```

**Verify**: `grep -c "None of the provided line item IDs exist" server/resources/event.py` → `2`.

### Step 3: Run tests

**Verify**: `cd server && uv run python -m pytest tests/test_event.py -v` → all pass.

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

### Step 4: Lint

**Verify**: `cd server && make lint` → exit 0.

## Test plan

Add two test cases to `server/tests/test_event.py`:

1. `test_event_creation_with_nonexistent_line_item_ids_returns_400`: POST to `/api/events`
   with a `line_items` array containing an ID that does not exist in the database.
   Assert response status is 400 and response body contains an `"error"` key.

2. `test_event_update_with_nonexistent_line_item_ids_returns_400`: Create an event,
   then PUT to `/api/events/<id>` with a `line_items` array of non-existent IDs.
   Assert response status is 400.

Use the `TestEventAPI` class and fixtures (`test_client`, `jwt_token`, `flask_app`,
`create_line_item_via_manual`, `create_event_via_api`) as the pattern — see
`server/tests/test_event.py:43-60` for the existing structure.

**Verify**: `cd server && uv run python -m pytest tests/test_event.py -v -k "nonexistent"` → 2 new tests pass.

## Done criteria

- [ ] `grep -c "None of the provided line item IDs exist" server/resources/event.py` → `2`
- [ ] `cd server && uv run python -m pytest -v` exits 0, 2 new tests pass
- [ ] Only `server/resources/event.py` and `server/tests/test_event.py` modified
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- The code around lines 74-75 or 118-119 in `event.py` has changed significantly —
  compare against "Current state" before proceeding.
- `get_line_item_amounts` is no longer the function used in the create path — report.
- Tests fail for reasons unrelated to this change.

## Maintenance notes

- If `get_line_item_amounts` is ever refactored to raise on empty results, remove
  these guards to avoid a duplicate check.
- The update path at lines 113-135 also validates other things; keep this guard
  consistent with those checks' response shapes.
