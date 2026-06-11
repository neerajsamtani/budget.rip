# Plan 018: Replace MongoDB-style filter syntax with SQLAlchemy idioms

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/dao.py server/resources/line_item.py server/resources/event.py`
> If any in-scope file changed, compare before proceeding.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: 006 (dedup tests must pass before touching data access code)
- **Category**: tech-debt
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

The MongoDB → PostgreSQL migration is complete, but `dao.py` and resource files
still use MongoDB operator syntax (`$in`, `$exists`) to build filter dicts that
are then interpreted by a custom adapter in `get_all_line_items`. This pattern:
1. Requires every developer to understand a non-standard "MongoDB-ish" filter DSL.
2. Only supports two operators (`$in`, `$exists`) — adding any other filter requires
   extending the adapter.
3. Confuses readers into thinking MongoDB may still be in use.

The fix replaces the dict-based filter pattern with direct SQLAlchemy query
parameters, which is the standard pattern already used in `get_all_events`
and `get_categorized_data`.

## Current state

**Three callsites that produce MongoDB-style dicts**:

`server/resources/line_item.py` (find the `only_line_items_to_review` handling):
```python
filters["event_id"] = {"$exists": False}    # ← MongoDB syntax
```

`server/resources/event.py:117`:
```python
filters: Dict[str, Any] = {"id": {"$in": update_data["line_items"]}}
```

`server/resources/event.py` also calls `get_line_item_amounts` (not `get_all_line_items`)
for some operations — check which function is called where.

**The interpreter in `server/dao.py:204-221`**:
```python
if "id" in filters:
    id_filter = filters["id"]
    if isinstance(id_filter, dict) and "$in" in id_filter:
        ids = [str(id) for id in id_filter["$in"]]
        query = query.filter(LineItem.id.in_(ids))

if "event_id" in filters:
    if isinstance(filters["event_id"], dict) and "$exists" in filters["event_id"]:
        if not filters["event_id"]["$exists"]:
            query = query.outerjoin(LineItem.events).filter(Event.id.is_(None))
```

**Target pattern**: `get_all_events` in `server/dao.py:254-280` uses direct
SQLAlchemy filters — use it as the exemplar.

## Commands you will need

| Purpose   | Command                                                              | Expected on success |
|-----------|----------------------------------------------------------------------|---------------------|
| Tests     | `cd server && uv run python -m pytest tests/test_line_item.py tests/test_event.py -v` | all pass |
| All tests | `cd server && uv run python -m pytest -v`                            | all pass |
| Lint      | `cd server && make lint`                                             | exit 0 |

## Scope

**In scope**:
- `server/dao.py` — `get_all_line_items` filter handling
- `server/resources/line_item.py` — filter construction
- `server/resources/event.py` — filter construction for update path

**Out of scope**:
- `server/utils/pg_bulk_ops.py` — no filter dict usage there.
- `get_all_events`, `get_categorized_data` — already use SQLAlchemy directly.
- Changing the public-facing query parameter names (e.g., `?payment_method=X`).

## Git workflow

- Branch: `advisor/018-remove-mongodb-filter-syntax`
- Commit message style: `Replace MongoDB-style filter syntax with SQLAlchemy idioms (#NNN)`

## Steps

### Step 1: Read all in-scope files in full

Read `server/dao.py:192-225`, `server/resources/line_item.py` in full, and
`server/resources/event.py:100-135` (update path). Map every place a filter
dict is constructed and where it is passed.

### Step 2: Redesign `get_all_line_items` to accept explicit parameters

Change the signature of `get_all_line_items` from:
```python
def get_all_line_items(filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
```
to:
```python
def get_all_line_items(
    ids: Optional[List[str]] = None,
    payment_method: Optional[str] = None,
    only_unreviewed: bool = False,
    limit: Optional[int] = None,   # from plan 010, if done
    offset: int = 0,
) -> List[Dict[str, Any]]:
```

Build the SQLAlchemy query using these parameters directly:
```python
if ids is not None:
    query = query.filter(LineItem.id.in_(ids))
if payment_method and payment_method != "All":
    query = query.join(LineItem.payment_method).filter(PaymentMethod.name == payment_method)
if only_unreviewed:
    query = query.outerjoin(LineItem.events).filter(Event.id.is_(None))
```

Remove the entire `if filters:` block.

**Verify after this step**: `cd server && uv run python -m pytest -v` — many tests
will fail at this point because callers still pass the old dict. That is expected;
fix all callers in subsequent steps.

### Step 3: Update all callers of `get_all_line_items`

Find all callers: `grep -rn "get_all_line_items" server/`

For each caller:
- If it passed `{"event_id": {"$exists": False}}` → pass `only_unreviewed=True`
- If it passed `{"id": {"$in": [...]}}` → pass `ids=[...]`
- If it passed `{"payment_method": "X"}` → pass `payment_method="X"`
- If it passed `None` or `{}` → call with no arguments (defaults)

Callers to check: `server/resources/line_item.py`, `server/resources/event.py`,
any other file returned by grep.

### Step 4: Remove the filter interpreter code from `dao.py`

Remove the entire `if filters:` block (lines ~204-222) from `get_all_line_items`.
Remove the `filters: Optional[Dict[str, Any]]` parameter.

**Verify**: `grep -n '"\$in"\|"\$exists"' server/` → 0 matches.

### Step 5: Run all tests

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

### Step 6: Lint

**Verify**: `cd server && make lint` → exit 0.

## Done criteria

- [ ] `grep -rn '"\$in"\|"\$exists"' server/` → 0 matches
- [ ] `get_all_line_items` no longer accepts a `Dict` filter argument
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] Only in-scope files modified
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- `get_all_line_items` is called with filter dicts from an unexpected place
  (beyond the 3 known callers) — map all callers before proceeding.
- The `date` filter in `get_all_events` uses a similar `$gte`/`$lte` dict pattern —
  this plan does NOT change `get_all_events`; leave that as a separate task.

## Maintenance notes

- After this change, new filters for `get_all_line_items` are added as explicit
  Python parameters with SQLAlchemy expressions — no more extending a custom DSL.
- If plan 010 (pagination) was already done and added `limit`/`offset` parameters
  to `get_all_line_items`, keep them in the new signature.
