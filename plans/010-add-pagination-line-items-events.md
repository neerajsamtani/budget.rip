# Plan 010: Add pagination to line items and events list endpoints

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/dao.py server/resources/line_item.py server/resources/event.py client/src/hooks/useApi.ts`
> If any in-scope file changed, compare before proceeding.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

`GET /api/line_items` and `GET /api/events` both call `query.all()` with no LIMIT.
As transactions accumulate (months/years of data), the server loads the entire
dataset into memory and serializes it all for every request. The client then
renders or filters everything in JavaScript. A user with a few years of data
could have 10k+ line items; each page load would become slow.

Adding optional `limit`/`offset` query parameters lets the client request only
what it needs. The review page (line items to review) already fetches a filtered
subset via `only_line_items_to_review`, so pagination is most critical for the
"all line items" and "events by date range" views.

## Current state

**Line items DAO** (`server/dao.py:192-225`):
```python
def get_all_line_items(filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ...
    query = query.order_by(LineItem.date.desc())
    line_items = query.all()          # ← no LIMIT
    return [serialize_line_item(li) for li in line_items]
```

**Events DAO** (`server/dao.py:254-281`):
```python
def get_all_events(filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ...
    events = query.order_by(Event.date.desc()).all()    # ← no LIMIT
    return [serialize_event(event) for event in events]
```

**Line items resource** (`server/resources/line_item.py` — read in full):
The GET handler extracts filters from query params and calls `get_all_line_items`.

**Events resource** (`server/resources/event.py:27-53`):
The GET handler extracts date filters and calls `get_all_events`.

**Client hook** (`client/src/hooks/useApi.ts` — search for `useLineItems` and `useEvents`):
These hooks call the API and return the full list. They would need to pass `limit`/`offset`
if pagination is added.

## Commands you will need

| Purpose   | Command                                                              | Expected on success |
|-----------|----------------------------------------------------------------------|---------------------|
| Server tests | `cd server && uv run python -m pytest tests/test_line_item.py tests/test_event.py -v` | all pass |
| All server   | `cd server && uv run python -m pytest -v`                            | all pass |
| Typecheck    | `cd client && npx tsc --noEmit`                                      | exit 0 |
| Client tests | `cd client && npm test -- --watchAll=false`                           | all pass |
| Lint (server)| `cd server && make lint`                                             | exit 0 |

## Scope

**In scope**:
- `server/dao.py` — `get_all_line_items` and `get_all_events`
- `server/resources/line_item.py` — extract and pass limit/offset
- `server/resources/event.py` — extract and pass limit/offset
- `server/tests/test_line_item.py` — add pagination tests
- `server/tests/test_event.py` — add pagination tests
- `client/src/hooks/useApi.ts` — update `useLineItems` and `useEvents` to accept limit/offset (optional, with sensible defaults)

**Out of scope**:
- Client UI components — do not add pagination UI controls in this plan; the
  client change is only to the hook API signature (adding optional params with
  defaults that preserve current behavior).
- Changing the response envelope shape — keep `{"data": [...]}`.

## Git workflow

- Branch: `advisor/010-add-pagination`
- Commit message style: `Add limit/offset pagination to line items and events endpoints (#NNN)`

## Steps

### Step 1: Update `get_all_line_items` to accept limit/offset

In `server/dao.py`, add `limit: Optional[int] = None` and `offset: int = 0`
parameters to `get_all_line_items`:

```python
def get_all_line_items(
    filters: Optional[Dict[str, Any]],
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    ...
    query = query.order_by(LineItem.date.desc())
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    line_items = query.all()
    return [serialize_line_item(li) for li in line_items]
```

Default `limit=None` means unlimited — preserving existing behavior for all
callers that don't pass a limit.

**Verify**: `cd server && uv run python -m pytest -v` → all pass (no behavior change with defaults).

### Step 2: Update `get_all_events` the same way

Add `limit: Optional[int] = None` and `offset: int = 0` to `get_all_events`.
Apply `.offset()` and `.limit()` before `.all()`, same pattern as step 1.

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

### Step 3: Extract limit/offset from query params in line_item resource

Read `server/resources/line_item.py` in full. In the GET endpoint handler,
extract optional `limit` and `offset` from `request.args`:

```python
limit = request.args.get("limit", type=int, default=None)
offset = request.args.get("offset", type=int, default=0)
```

Pass them through to `get_all_line_items(filters, limit=limit, offset=offset)`.

**Verify**: `curl "http://localhost:5000/api/line_items?limit=10&offset=0"` returns
10 items (manual test, skip if server not running; confirm via test in step 6).

### Step 4: Extract limit/offset in events resource

Same pattern in the GET handler in `server/resources/event.py`.

### Step 5: Update client hooks (optional parameters, backward-compatible)

In `client/src/hooks/useApi.ts`, find `useLineItems` and `useEvents`. Add optional
`limit?: number` and `offset?: number` to their options/params type. Pass them
as query parameters to the API if provided. Keep existing calls unchanged (no
breaking change).

**Verify**: `cd client && npx tsc --noEmit` → exit 0.

### Step 6: Add pagination tests

In `server/tests/test_line_item.py`:
- Create 5 line items, call `/api/line_items?limit=2` → assert 2 items returned.
- Call `/api/line_items?limit=2&offset=2` → assert 2 different items (page 2).
- Call `/api/line_items` (no params) → assert all 5 items returned.

Add equivalent tests in `server/tests/test_event.py`.

**Verify**: `cd server && uv run python -m pytest tests/test_line_item.py tests/test_event.py -v -k "pagination"` → new tests pass.

### Step 7: Final verification

**Verify**: `cd server && uv run python -m pytest -v` → all pass.
**Verify**: `cd client && npm test -- --watchAll=false` → all pass.
**Verify**: `cd server && make lint` → exit 0.

## Done criteria

- [ ] `get_all_line_items` and `get_all_events` accept optional `limit`/`offset`
- [ ] Line items and events GET endpoints read `limit`/`offset` from query params
- [ ] Calling without params returns the same results as before (no behavior change)
- [ ] Pagination tests exist and pass for both endpoints
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] `cd client && npx tsc --noEmit` exits 0
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- `get_all_line_items` is called from somewhere other than the resource file that
  passes hardcoded positional args — check all callers with
  `grep -rn "get_all_line_items" server/` before changing the signature.
- The client `useLineItems` or `useEvents` hooks are used by components that
  would break if the response shape changes — the shape must stay the same.

## Maintenance notes

- Default `limit=None` (unlimited) preserves current behavior. A future product
  decision may want a default limit (e.g., 500) to bound unintentional full-scans —
  that's a separate change requiring client pagination UI.
- The events page uses date-range filtering server-side; for most users, this
  naturally bounds results to one month. Pagination is most valuable for the
  "all line items" view.
