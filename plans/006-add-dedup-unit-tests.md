# Plan 006: Add unit tests for bulk_upsert_line_items deduplication logic

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/utils/pg_bulk_ops.py`
> If `pg_bulk_ops.py` changed, read the current version before writing tests.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: tests
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

`bulk_upsert_line_items()` in `server/utils/pg_bulk_ops.py` is the most critical
function in the codebase: it prevents duplicate line items on every API re-import,
updates changed fields on existing items, and deliberately skips items already
reviewed into an event. This logic is 127 lines long (lines 214-341) with no
direct unit tests. Integration tests (test_venmo, test_stripe, test_splitwise) call
the full refresh pipeline and would catch gross failures, but subtle regressions
in the dedup logic (e.g., the `evented_line_item_ids` guard, the update-if-changed
check, the missing-transaction skip) would not surface.

## Current state

`server/utils/pg_bulk_ops.py` — bulk operations for PostgreSQL.

Key behavior to test (`server/utils/pg_bulk_ops.py:214-341`):

1. **Insert path** (lines 299-336): new line items with a valid `source_id` that has
   a matching transaction are bulk-inserted.
2. **Update path** (lines 304-309): if `existing_li.id not in evented_line_item_ids`,
   the existing line item is updated if any field changed.
3. **Skip evented** (lines 306-309): if the line item is already in an event, it is
   never updated.
4. **Skip missing transaction** (lines 316-319): if no transaction matches `source_id`,
   the line item is skipped with a warning log.

`server/resources/line_item.py` — `LineItem` data transfer object (the input type
to `bulk_upsert_line_items`). Constructor: `LineItem(date, responsible_party,
payment_method, description, amount, source_id=...)`.

`server/tests/conftest.py` — test infrastructure. Uses SQLite in-memory DB.
All tests get a fresh DB per test (tables created/destroyed). Key fixtures:
- `test_client` — Flask test client
- `jwt_token` — valid JWT
- `flask_app` — app context
- `create_line_item_via_manual` — helper to create line items via the API

## Commands you will need

| Purpose   | Command                                                        | Expected on success |
|-----------|----------------------------------------------------------------|---------------------|
| New tests | `cd server && uv run python -m pytest tests/test_pg_bulk_ops.py -v` | all pass |
| All tests | `cd server && uv run python -m pytest -v`                      | all pass |
| Lint      | `cd server && make lint`                                       | exit 0 |

## Scope

**In scope**:
- `server/tests/test_pg_bulk_ops.py` (new file to create)

**Out of scope**:
- `server/utils/pg_bulk_ops.py` — read only, do not modify it.
- Any existing test file.

## Git workflow

- Branch: `advisor/006-add-dedup-unit-tests`
- Commit message style: `Add unit tests for bulk_upsert_line_items deduplication (#NNN)`

## Steps

### Step 1: Understand the test infrastructure

Read `server/tests/conftest.py` in full. Note:
- The `flask_app` fixture provides an app context.
- Tests use SQLite in-memory DB with the same SQLAlchemy models.
- Look for a fixture that provides a database session directly (e.g., a `db_session`
  fixture, or access via `flask_app.app_context()`). If no `db_session` fixture
  exists, you'll need to import `SessionLocal` from `models.database` inside an
  `app_context()`.

Also read `server/tests/test_venmo.py` for examples of how the existing integration
tests set up transactions and line items — use that as a structural pattern.

### Step 2: Create `server/tests/test_pg_bulk_ops.py`

Create the file with the following test class and cases. Each test is independent
and should set up its own transactions/line items.

```python
"""Unit tests for bulk_upsert_line_items deduplication logic."""
import pytest

from resources.line_item import LineItem
from utils.pg_bulk_ops import bulk_upsert_line_items


class TestBulkUpsertLineItems:
    # Helper: create a LineItem DTO
    def _make_li(self, source_id, description="Test", amount=10.0):
        return LineItem(
            date=1700000000.0,
            responsible_party="Test Party",
            payment_method="Unknown",
            description=description,
            amount=amount,
            source_id=source_id,
        )
```

**Test cases to implement** (these are specifications — implement each):

**test_new_line_item_is_inserted**:
- Pre-condition: a Transaction row exists with `source="venmo_api"` and
  `source_id="test_src_1"`.
- Call `bulk_upsert_line_items(db, [li], source="venmo_api")` where `li.source_id = "test_src_1"`.
- Assert return value is 1.
- Assert one `LineItem` row exists in the DB with `description="Test"`.

**test_duplicate_source_id_is_not_reinserted**:
- Pre-condition: Transaction + LineItem already exist for `source_id="test_src_2"`.
- Call `bulk_upsert_line_items(db, [li], source="venmo_api")` again with same source_id.
- Assert return value is 0 (no new inserts).
- Assert still exactly 1 `LineItem` row for that transaction.

**test_changed_line_item_is_updated**:
- Pre-condition: Transaction + LineItem exist for `source_id="test_src_3"` with
  `description="Old Description"`.
- Call with `description="New Description"`.
- Assert `LineItem.description` is now `"New Description"`.

**test_evented_line_item_is_never_updated**:
- Pre-condition: Transaction + LineItem exist for `source_id="test_src_4"`,
  and that LineItem is linked to an Event via `EventLineItem`.
- Call with changed description.
- Assert `LineItem.description` is still the original value (not updated).

**test_missing_transaction_is_skipped**:
- No Transaction row for `source_id="test_src_5"`.
- Call `bulk_upsert_line_items(db, [li], source="venmo_api")`.
- Assert return value is 0 and no LineItem exists for that source_id.

**Patterns for creating DB rows**: import the SQLAlchemy models directly and
use the session to add rows, e.g.:
```python
from models.sql_models import Transaction, LineItem as LineItemModel, Event, EventLineItem, Category, PaymentMethod
```

Use `flask_app` fixture to get an app context, then `SessionLocal` from
`models.database` to create a session.

**Verify**: `cd server && uv run python -m pytest tests/test_pg_bulk_ops.py -v` → 5 tests pass.

### Step 3: Run all tests to confirm no regressions

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

### Step 4: Lint

**Verify**: `cd server && make lint` → exit 0.

## Done criteria

- [ ] `server/tests/test_pg_bulk_ops.py` exists with at least 5 test functions
- [ ] All 5 test functions pass: new_insert, duplicate_skip, changed_update, evented_skip, missing_transaction_skip
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] Only `server/tests/test_pg_bulk_ops.py` created (no other files modified)
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- `conftest.py` does not have a database session fixture and you cannot figure out
  how to get a raw session in tests — read `test_venmo.py` carefully for the pattern,
  then report if still stuck.
- `bulk_upsert_line_items` requires session state (e.g., flushed payment methods)
  that is not obvious from reading the function — report rather than guessing.

## Maintenance notes

- These tests are the safety net for plan 018 (remove MongoDB filter syntax),
  plan 019 (dao split), and plan 022 (integration refactor). They must pass before
  any of those plans touch `pg_bulk_ops.py`.
- If `bulk_upsert_line_items` signature changes, update these tests first.
