# Plan 004: Use Decimal accumulation in monthly breakdown to avoid float rounding

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/dao.py`
> If `dao.py` changed, compare the "Current state" excerpts before proceeding.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

Amounts are stored as `DECIMAL(12,2)` in PostgreSQL. SQLAlchemy returns `Decimal`
objects for these columns. The monthly breakdown accumulates them with
`breakdown[key] += float(row.amount or 0)` — converting to `float` first.
Repeated float addition accumulates rounding errors; a user with many transactions
in one category may see a monthly total off by a penny or more. For a budget app
this erodes trust. The fix is to keep `Decimal` throughout and convert to `float`
only at the JSON serialization boundary.

## Current state

`server/dao.py` — data access layer.

**Bug site** (`server/dao.py:104-114`):
```python
breakdown: Dict[tuple, float] = defaultdict(float)
for row in rows:
    if not row.category:
        continue
    utc_date = row.date.astimezone(tz.utc) if row.date.tzinfo else row.date.replace(tzinfo=tz.utc)
    key = (utc_date.year, utc_date.month, row.category)
    breakdown[key] += float(row.amount or 0)   # ← converts Decimal → float before summing

return [
    {"year": year, "month": month, "category": category, "totalExpense": amount}
    for (year, month, category), amount in sorted(breakdown.items())
]
```

`row.amount` comes from a SQLAlchemy `case()` expression that resolves to
`func.sum(LineItem.amount)` or `func.min(LineItem.amount)` — both return `Decimal`
when the underlying column is `DECIMAL(12,2)`.

**Pattern to follow**: `server/dao.py:162` — `serialize_event` already does the
right thing: `amount = float(event.total_amount) if event.total_amount else 0.0`
(converts at serialization time, not during accumulation).

## Commands you will need

| Purpose   | Command                                           | Expected on success |
|-----------|---------------------------------------------------|---------------------|
| Tests     | `cd server && uv run python -m pytest tests/test_monthly_breakdown.py -v` | all pass |
| All tests | `cd server && uv run python -m pytest -v`         | all pass |
| Lint      | `cd server && make lint`                          | exit 0 |

## Scope

**In scope**:
- `server/dao.py` — `get_categorized_data()` only

**Out of scope**:
- `serialize_line_item`, `serialize_event`, or any other function in `dao.py`.
- The monthly breakdown resource file (`server/resources/monthly_breakdown.py`).

## Git workflow

- Branch: `advisor/004-fix-decimal-money-math`
- Commit message style: `Use Decimal accumulation in monthly breakdown (#NNN)`

## Steps

### Step 1: Change breakdown dict type and accumulation

In `server/dao.py`, inside `get_categorized_data()`, make three changes:

1. Import `Decimal` at the top of the function (it's already imported at module
   level via `from decimal import Decimal` if present, or add `from decimal import Decimal`
   at the top of the file if missing).

   Check: `grep "from decimal import" server/dao.py` — if absent, add it at the
   top of the file alongside the existing imports.

2. Change the `breakdown` dict type annotation from `float` to `Decimal`:
   ```python
   breakdown: Dict[tuple, Decimal] = defaultdict(Decimal)
   ```

3. Change the accumulation line from:
   ```python
   breakdown[key] += float(row.amount or 0)
   ```
   to:
   ```python
   breakdown[key] += row.amount if row.amount is not None else Decimal("0")
   ```

4. Convert to `float` at serialization in the return statement:
   ```python
   return [
       {"year": year, "month": month, "category": category, "totalExpense": float(amount)}
       for (year, month, category), amount in sorted(breakdown.items())
   ]
   ```

**Verify**: `grep "float(row.amount" server/dao.py` → no matches.

### Step 2: Run tests

**Verify**: `cd server && uv run python -m pytest tests/test_monthly_breakdown.py -v` → all pass.

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

### Step 3: Lint

**Verify**: `cd server && make lint` → exit 0.

## Test plan

In `server/tests/test_monthly_breakdown.py`, add a test that:
1. Creates multiple line items in the same month/category with amounts that would
   exhibit float rounding (e.g., `Decimal("0.10")` × 3 = `0.30` but
   `0.1 + 0.1 + 0.1` in float ≠ `0.3` exactly).
2. Calls the `/api/monthly_breakdown` endpoint.
3. Asserts the returned `totalExpense` value is correct to 2 decimal places.

Use existing tests in `test_monthly_breakdown.py` as the structural pattern.

**Verify**: `cd server && uv run python -m pytest tests/test_monthly_breakdown.py -v -k "decimal"` → 1 new test passes.

## Done criteria

- [ ] `grep "float(row.amount" server/dao.py` returns no matches
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] Only `server/dao.py` and `server/tests/test_monthly_breakdown.py` modified
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- SQLite (the test database) handles `Decimal` differently from PostgreSQL — if
  tests fail because `row.amount` is a `float` in the test environment, use
  `Decimal(str(row.amount))` instead of bare `row.amount`. Report the discovery.
- The `rows` query result type has changed (e.g., `row.amount` is no longer a
  `Decimal` or SQL aggregation type) — report before changing the accumulation.

## Maintenance notes

- The `serialize_line_item` and `serialize_event` functions do `float(li.amount)`
  at serialization time — this is correct and should not be changed; amounts are
  converted once per item, not summed as floats.
- If the monthly breakdown endpoint ever returns raw Decimal values in JSON
  (Python's `json` module cannot serialize Decimal directly), a `JSONEncoder`
  subclass or `float()` conversion at the boundary is needed. The current
  `float(amount)` in the return statement handles this.
