# Plan 001: Fix Stripe line item responsible_party field assignment

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/resources/stripe.py`
> If `stripe.py` changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

Every Stripe-sourced line item is created with `description` in both the
`responsible_party` and `description` fields. The `responsible_party` field
is used in the review UI, analytics, and filtering — for all Stripe
transactions it shows the transaction description (e.g., "Amazon Marketplace")
instead of the account owner or an empty value. Stripe's API has no
"responsible party" concept, so the correct value is an empty string or the
bank account's display name.

## Current state

`server/resources/stripe.py` — Stripe data ingestion. The `stripe_to_line_items()`
function constructs `LineItem` objects.

`server/resources/line_item.py` — defines the `LineItem` data transfer object.

**LineItem constructor** (`server/resources/line_item.py:29-38`):
```python
def __init__(
    self,
    date: float,
    responsible_party: str,   # positional arg 2
    payment_method: str,       # positional arg 3
    description: str,          # positional arg 4
    amount: float,
    ...
```

**Bug site** (`server/resources/stripe.py:370-377`):
```python
line_item = LineItem(
    stripe_transaction["transacted_at"],   # date ✓
    stripe_transaction["description"],      # responsible_party ← WRONG: should be ""
    payment_method,                         # payment_method ✓
    stripe_transaction["description"],      # description ✓
    flip_amount(stripe_transaction["amount"]) / 100,
    source_id=str(stripe_transaction["source_id"]),
)
```

**Repo convention**: The other integrations show what `responsible_party` should be:
- Venmo: `server/resources/venmo.py` passes the Venmo username/contact name
- Splitwise: `server/resources/splitwise.py` passes the Splitwise user name
- Stripe has no per-transaction party concept; `""` is the correct empty value.

## Commands you will need

| Purpose   | Command                             | Expected on success |
|-----------|-------------------------------------|---------------------|
| Tests     | `cd server && uv run python -m pytest tests/test_stripe.py -v` | all pass |
| All tests | `cd server && uv run python -m pytest -v` | all pass |
| Lint      | `cd server && make lint`            | exit 0 |

## Scope

**In scope**:
- `server/resources/stripe.py` (the one-line fix)

**Out of scope**:
- Existing Stripe line items in the database — this plan does not backfill data.
  If backfilling is needed, that is a separate database migration task.
- Any other integration file.

## Git workflow

- Branch: `advisor/001-fix-stripe-line-item-fields`
- Commit message style: `Fix Stripe line item responsible_party field (#NNN)`

## Steps

### Step 1: Fix the field assignment

In `server/resources/stripe.py`, change line 372 from:
```python
    stripe_transaction["description"],      # responsible_party (WRONG)
```
to:
```python
    "",      # responsible_party: Stripe has no per-transaction party
```

The full `LineItem(...)` call after the fix should be:
```python
line_item = LineItem(
    stripe_transaction["transacted_at"],
    "",                                        # responsible_party
    payment_method,
    stripe_transaction["description"],
    flip_amount(stripe_transaction["amount"]) / 100,
    source_id=str(stripe_transaction["source_id"]),
)
```

**Verify**: `grep -n 'stripe_transaction\["description"\]' server/resources/stripe.py`
→ should return exactly **one** match (the `description` positional argument at line 374), not two.

### Step 2: Run tests

**Verify**: `cd server && uv run python -m pytest tests/test_stripe.py -v` → all existing tests pass.

**Verify**: `cd server && uv run python -m pytest -v` → all tests pass.

### Step 3: Lint

**Verify**: `cd server && make lint` → exit 0.

## Test plan

Add one test to `server/tests/test_stripe.py` verifying that a Stripe line item
is created with an empty `responsible_party`. Use the existing test structure in
that file as a pattern (look for the `TestStripeAPI` class or the `test_stripe_*`
functions, whichever is present).

The test should:
1. Call the stripe-to-line-items path with mock transaction data.
2. Assert the resulting line item's `responsible_party` is `""` (not the description string).

**Verify**: `cd server && uv run python -m pytest tests/test_stripe.py -v -k "responsible_party"` → 1 new test passes.

## Done criteria

- [ ] `grep -n '"description"\],\s*#.*responsible' server/resources/stripe.py` returns no matches
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] No files outside `server/resources/stripe.py` and `server/tests/test_stripe.py` are modified
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- The `LineItem.__init__` signature at `server/resources/line_item.py:29-38` has changed
  (different parameter order or names) — the fix may need to change.
- Stripe tests fail for a reason unrelated to this change — report before proceeding.
- The codebase uses `responsible_party` for Stripe data somewhere else in a way that
  would break if it becomes empty — report and await guidance.

## Maintenance notes

- **Existing data**: All previously ingested Stripe line items in production have
  `responsible_party` set to the description string. A future cleanup migration could
  set them to `""` if desired, but it's purely cosmetic.
- **Future Stripe fields**: If Stripe ever provides a counterparty name, update
  `stripe_to_line_items()` here to populate it.
