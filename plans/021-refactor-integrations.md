# Plan 021: Extract common fetch-transform-upsert pipeline from data source integrations

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/resources/venmo.py server/resources/splitwise.py server/resources/stripe.py`
> If any changed significantly, re-read them before proceeding.

## Status

- **Priority**: P3
- **Effort**: L
- **Risk**: MED
- **Depends on**: 006 (dedup tests must exist), 019 (dao split should be stable), 020 (exception handling done)
- **Category**: tech-debt
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

Venmo, Splitwise, and Stripe each implement the same conceptual pipeline:
1. Fetch raw API data → store in `transactions` table
2. Read stored transactions → transform to `LineItem` objects
3. Bulk upsert line items

The implementations are independent, and each change to the pipeline (adding a field,
changing dedup logic, improving error handling) must be made in 3 places. Extracting
a shared base class or protocol reduces this to 1 place while keeping the
source-specific logic (API clients, field mapping) isolated.

**This is a large, risky refactor. Do not start it without all dependency plans done.**

## Current state

Read all three files before starting:
- `server/resources/venmo.py` — `refresh_venmo()` and `venmo_to_line_items()`
- `server/resources/splitwise.py` — `refresh_splitwise()` and `splitwise_to_line_items()`
- `server/resources/stripe.py` — `refresh_stripe()` and `stripe_to_line_items()`

Each follows this pattern:
```python
def refresh_<source>():
    # 1. Call external API client
    # 2. Store raw data via bulk_upsert_transactions(db, data, source="<source>_api")

def <source>_to_line_items():
    # 1. Read stored transactions via get_transactions("<source>_api", None)
    # 2. Map each transaction dict to a LineItem object
    # 3. Batch and call bulk_upsert_line_items(db, batch, source="<source>_api")
```

## Commands you will need

| Purpose   | Command                                                                                    | Expected on success |
|-----------|--------------------------------------------------------------------------------------------|---------------------|
| Tests     | `cd server && uv run python -m pytest tests/test_venmo.py tests/test_splitwise.py tests/test_stripe.py tests/test_pg_bulk_ops.py -v` | all pass |
| All tests | `cd server && uv run python -m pytest -v`                                                  | all pass |
| Lint      | `cd server && make lint`                                                                   | exit 0 |

## Scope

**In scope**:
- `server/utils/integrations.py` (new file)
- `server/resources/venmo.py`
- `server/resources/splitwise.py`
- `server/resources/stripe.py`

**Out of scope**:
- `server/resources/manual_transaction.py` — manual transactions bypass the
  pipeline intentionally (no external API).
- `server/utils/pg_bulk_ops.py` — do not change it.
- The API endpoint handlers (routes) — only the underlying functions change.

## Git workflow

- Branch: `advisor/021-refactor-integrations`
- Commit message style: `Extract shared integration pipeline to utils/integrations.py (#NNN)`

## Steps

### Step 1: Design the shared interface

Create `server/utils/integrations.py` with a base class:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class DataSourceIntegration(ABC):
    """Base class for external data source integrations (Venmo, Splitwise, Stripe)."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """e.g. 'venmo_api', 'splitwise_api', 'stripe_api'"""
        ...

    @abstractmethod
    def fetch_and_store(self) -> None:
        """Fetch from external API and store raw data in transactions table."""
        ...

    @abstractmethod
    def transactions_to_line_items(self, transactions: List[Dict[str, Any]]) -> List[Any]:
        """Transform stored transaction dicts to LineItem objects."""
        ...

    def sync(self) -> None:
        """Full pipeline: fetch → store → transform → upsert."""
        from dao import get_transactions
        from models.database import SessionLocal
        from utils.pg_bulk_ops import bulk_upsert_line_items, BATCH_SIZE

        self.fetch_and_store()
        transactions = get_transactions(self.source_name, None)
        batch = []
        for txn in transactions:
            items = self.transactions_to_line_items([txn])
            batch.extend(items)
            if len(batch) >= BATCH_SIZE:
                with SessionLocal.begin() as db:
                    bulk_upsert_line_items(db, batch, source=self.source_name)
                batch = []
        if batch:
            with SessionLocal.begin() as db:
                bulk_upsert_line_items(db, batch, source=self.source_name)
```

### Step 2: Migrate one integration at a time — start with Venmo

Implement `VenmoIntegration(DataSourceIntegration)` in `venmo.py`. Move the logic
from `venmo_to_line_items()` into `transactions_to_line_items()`. Keep existing
functions as thin wrappers calling `VenmoIntegration().sync()` for one release
cycle, then remove them.

**Verify after each integration**: `cd server && uv run python -m pytest tests/test_venmo.py -v` → all pass.

### Step 3: Migrate Splitwise

Same as step 2 for `splitwise.py`.

**Verify**: `cd server && uv run python -m pytest tests/test_splitwise.py -v` → all pass.

### Step 4: Migrate Stripe

Same pattern. Stripe is more complex (pagination, account lookup) — keep the
complexity in the `fetch_and_store` method.

**Verify**: `cd server && uv run python -m pytest tests/test_stripe.py -v` → all pass.

### Step 5: Run full test suite

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

### Step 6: Lint

**Verify**: `cd server && make lint` → exit 0.

## Done criteria

- [ ] `server/utils/integrations.py` exists with `DataSourceIntegration` base class
- [ ] Venmo, Splitwise, and Stripe each implement it
- [ ] All existing integration tests pass
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- The Stripe integration's `refresh_transactions` and `stripe_to_line_items` are
  more tightly coupled than the base pattern accommodates (e.g., they share state
  across calls) — report the coupling before proceeding; a forced fit is worse
  than leaving Stripe out of the refactor for now.
- A test fails after migrating one integration but not others — fix it before
  moving to the next integration.

## Maintenance notes

- Adding a new data source: subclass `DataSourceIntegration`, implement the two
  abstract methods, call `.sync()` from the refresh endpoint.
- The `BATCH_SIZE` constant in `pg_bulk_ops.py` controls memory usage during
  transformation; the base `sync()` method respects it automatically.
