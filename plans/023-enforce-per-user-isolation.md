# Plan 023: Enforce explicit per-user data isolation in DAO queries

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/dao.py server/models/sql_models.py`
> If either changed significantly, re-read before proceeding.

## Status

- **Priority**: P3
- **Effort**: L
- **Risk**: HIGH
- **Depends on**: 019 (dao split — queries should be in queries.py by then), 022 (tags user_id done)
- **Category**: security
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

Data isolation currently relies on a transitive join chain:
`Event.category_id → Category.user_id`. If an `Event` somehow gains a category
from another user, or if a new query path omits the category join, another user's
data becomes visible. For a single-user app this is theoretical; for multi-user
it is a security boundary.

This plan adds **explicit** `user_id` filtering to the core query functions.
Because it touches the most-used DAO functions and requires understanding the
full join chain, the risk is HIGH. Do not execute without the dependency plans done.

## Current state

**Schema**: `Event` has `category_id → Category.user_id`. No direct `user_id` on `Event` or `LineItem`.
**Isolation method**: implicit — events are scoped by the user who owns the Category.

The main query functions (in `dao.py`, or `queries.py` if plan 019 is done):
- `get_all_events(filters)` — no user_id parameter
- `get_all_line_items(...)` — no user_id parameter
- `get_categorized_data()` — no user_id parameter

`get_current_user()` is available via `flask_jwt_extended` in resource functions.

## Commands you will need

| Purpose   | Command                                 | Expected on success |
|-----------|-----------------------------------------|---------------------|
| Tests     | `cd server && uv run python -m pytest -v` | all pass |
| Lint      | `cd server && make lint`                | exit 0 |

## Scope

**In scope**:
- `server/queries.py` (or `server/dao.py` if plan 019 not done) — query functions
- `server/domain.py` (or `server/dao.py`) — `get_categorized_data`
- `server/resources/event.py`, `server/resources/line_item.py`,
  `server/resources/monthly_breakdown.py` — pass user_id from JWT to DAO functions

**Out of scope**:
- Client code.
- Auth endpoints.
- The `users` table itself — no schema changes.
- Adding `user_id` FK to `Event` or `LineItem` models — that is a large schema
  migration. This plan uses the existing join chain, just makes it explicit.

## Git workflow

- Branch: `advisor/023-enforce-per-user-isolation`
- Commit message style: `Enforce explicit per-user filtering in DAO queries (#NNN)`

## Steps

### Step 1: Map the current join chain for events

Read `get_all_events` in full. Confirm: `Event.category_id → Category.user_id`.
The query already joins `Category` via `joinedload`. Add an explicit filter:

```python
def get_all_events(filters, user_id: str, ...):
    ...
    query = query.join(Event.category).filter(Category.user_id == user_id)
    ...
```

### Step 2: Update all callers to pass user_id

In `server/resources/event.py`, every endpoint that calls `get_all_events`:
```python
user = get_current_user()
events = get_all_events(filters, user_id=user["id"])
```

Find all callers: `grep -rn "get_all_events" server/`.

### Step 3: Add user_id filtering to get_categorized_data

`get_categorized_data()` already joins `Category` — add
`.filter(Category.user_id == user_id)` to the main query. Update the function
signature to accept `user_id: str`.

Update the caller in `server/resources/monthly_breakdown.py`.

### Step 4: Add user_id filtering to get_all_line_items

Line items do not have a direct `user_id`. The join path is:
`LineItem.transaction_id → (implicit: line items are created from transactions that
are associated with a user's integration)`.

Since there is no direct FK from `LineItem` to `User`, filter through events:
include only line items that either (a) have no event yet, OR (b) belong to an
event with a category owned by the user.

This is complex — read the query in `get_all_line_items` and model after how
`only_unreviewed=True` works (outer join + filter). Document the approach clearly.

**Alternatively (simpler)**: For the review queue (unreviewed line items), there
is no user association yet by definition. Accept this limitation for now and add
a note in the code; add user_id to `LineItem` model in a follow-up migration
instead.

### Step 5: Run all tests

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

### Step 6: Lint

**Verify**: `cd server && make lint` → exit 0.

## Done criteria

- [ ] `get_all_events` and `get_categorized_data` require and use `user_id` parameter
- [ ] All callers pass `user_id` from `get_current_user()`
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- The join chain for line items is too complex to filter by user without a schema
  change (adding `user_id` FK to `LineItem`) — document this and stop; report
  the finding. Do not implement a fragile workaround.
- Any test failure after adding `user_id` filters — investigate before proceeding;
  test data may lack `user_id` on categories, causing empty results.

## Maintenance notes

- The cleanest long-term solution is adding `user_id` directly to `Event` and
  `LineItem` via Alembic migrations. The current transitive approach is a stopgap.
- When multi-user support is added, add integration tests that verify user A's
  data is not visible to user B.
