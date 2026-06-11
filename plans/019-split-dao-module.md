# Plan 019: Split dao.py into queries, serializers, and domain modules

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/dao.py`
> If it changed significantly, re-read the file before proceeding.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: LOW
- **Depends on**: 006 (tests must exist to catch regressions), 018 (filter API should be stable before splitting)
- **Category**: tech-debt
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

`server/dao.py` is 470 lines containing four distinct concerns: serialization
helpers (`serialize_*`), read queries (`get_*`), write operations (`create_*`,
`delete_*`), and domain logic (`get_categorized_data`, `get_line_item_amounts`,
`remove_event_from_line_item`). Finding the right function requires scanning the
whole file. Splitting by concern makes each module focused and scannable.

## Current state

`server/dao.py` — 470 lines, 18 public functions. Contents:

**Serializers** (functions that convert ORM objects to dicts):
- `serialize_datetime` (line 118)
- `serialize_line_item` (line 129)
- `serialize_user` (line 149)
- `serialize_event` (line 160)

**Read queries** (functions that query the DB and return dicts):
- `get_user_by_email` (line 32)
- `get_user_by_id` (line 243)
- `get_all_line_items` (line 192)
- `get_line_item_by_id` (line 228)
- `get_all_events` (line 254)
- `get_event_by_id` (line 284)
- `get_transactions` (line 300)
- `get_all_bank_accounts` (line 325)
- `get_payment_method_by_id` (line 456)

**Domain logic** (business-level operations):
- `get_categorized_data` (line 49)
- `get_line_item_amounts` (line 178)
- `remove_event_from_line_item` (line 13)

**Write operations**:
- `create_manual_transaction` (line 355)
- `delete_manual_transaction` (line 416)

**Target structure**:
```
server/
  dao.py              ← thin re-export facade (backward compat during transition)
  serializers.py      ← serialize_datetime, serialize_line_item, serialize_user, serialize_event
  queries.py          ← all get_* read functions
  domain.py           ← get_categorized_data, get_line_item_amounts, remove_event_from_line_item,
                        create_manual_transaction, delete_manual_transaction
```

## Commands you will need

| Purpose   | Command                                 | Expected on success |
|-----------|-----------------------------------------|---------------------|
| Tests     | `cd server && uv run python -m pytest -v` | all pass |
| Lint      | `cd server && make lint`                | exit 0 |

## Scope

**In scope**:
- `server/dao.py`
- `server/serializers.py` (new)
- `server/queries.py` (new)
- `server/domain.py` (new)

**Out of scope**:
- All callers of functions from `dao.py` (resources, utils, application.py) —
  keep backward compatibility via re-exports in `dao.py` itself. Do NOT update
  import statements in other files in this plan.

## Git workflow

- Branch: `advisor/019-split-dao-module`
- Commit message style: `Split dao.py into serializers, queries, and domain modules (#NNN)`

## Steps

### Step 1: Create `server/serializers.py`

Move `serialize_datetime`, `serialize_line_item`, `serialize_user`,
`serialize_event` to a new file `server/serializers.py`.

Each function needs its imports (SQLAlchemy models, datetime, etc.) — copy the
relevant imports from `dao.py`.

### Step 2: Create `server/queries.py`

Move all `get_*` read functions to `server/queries.py`. These functions import
from `models.database` and `models.sql_models` inline (inside the function body
in `dao.py`) — keep the same inline import pattern in `queries.py`. Import
`serialize_*` functions from `serializers.py`.

### Step 3: Create `server/domain.py`

Move `get_categorized_data`, `get_line_item_amounts`, `remove_event_from_line_item`,
`create_manual_transaction`, `delete_manual_transaction` to `server/domain.py`.
Import serializers from `serializers.py` where needed.

### Step 4: Update `server/dao.py` to re-export everything

Replace the body of `dao.py` with re-exports so all existing callers continue
to work:
```python
# Re-exports for backward compatibility — callers should migrate to direct imports
from serializers import serialize_datetime, serialize_line_item, serialize_user, serialize_event
from queries import (
    get_user_by_email, get_user_by_id, get_all_line_items, get_line_item_by_id,
    get_all_events, get_event_by_id, get_transactions, get_all_bank_accounts,
    get_payment_method_by_id,
)
from domain import (
    get_categorized_data, get_line_item_amounts, remove_event_from_line_item,
    create_manual_transaction, delete_manual_transaction,
)
```

**Verify**: `cd server && uv run python -m pytest -v` → all pass (no import errors).

### Step 5: Lint

**Verify**: `cd server && make lint` → exit 0.

## Done criteria

- [ ] `server/serializers.py`, `server/queries.py`, `server/domain.py` exist
- [ ] `server/dao.py` is a thin re-export file (< 30 lines)
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] No callers outside `dao.py` were modified (grep: `grep -rn "from dao import" server/resources/` should still resolve correctly)
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- Circular imports arise (e.g., `domain.py` imports from `queries.py` which imports
  from `serializers.py` which imports a model that somehow imports back) — resolve
  by moving shared imports to a common location or using inline imports.
- Test failures after moving functions — check imports in the new files carefully.

## Maintenance notes

- `dao.py` re-exports are for backward compatibility only. After this plan, new
  code should import directly from `serializers`, `queries`, or `domain`.
- A future cleanup plan can update all resource files to use the direct imports
  and remove `dao.py` entirely.
