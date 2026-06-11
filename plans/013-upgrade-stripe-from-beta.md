# Plan 013: Upgrade Stripe SDK from beta to stable release

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/pyproject.toml`
> If it changed, verify the Stripe version before proceeding.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: deps
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

`server/pyproject.toml:42` pins `stripe==14.1.0b1` — a beta release. Beta releases
may be removed from PyPI, lack production guarantees, and can introduce breaking
changes before the final release. If a stable 14.x is available, upgrading removes
this risk with minimal effort.

## Current state

`server/pyproject.toml:42`:
```
"stripe==14.1.0b1",
```

## Commands you will need

| Purpose    | Command                                                           | Expected on success |
|------------|-------------------------------------------------------------------|---------------------|
| Check PyPI | `pip index versions stripe 2>/dev/null \| head -3` or check `https://pypi.org/pypi/stripe/json` | shows latest version |
| Update     | `cd server && uv add stripe==<version>`                           | exit 0 |
| Tests      | `cd server && uv run python -m pytest -v`                         | all pass |
| Lint       | `cd server && make lint`                                          | exit 0 |

## Scope

**In scope**:
- `server/pyproject.toml`
- `server/uv.lock` (updated automatically by uv)

**Out of scope**:
- `server/resources/stripe.py` — do not change the Stripe SDK usage unless the
  upgrade has a breaking API change (see STOP conditions).

## Git workflow

- Branch: `advisor/013-upgrade-stripe-from-beta`
- Commit message style: `Upgrade Stripe SDK to stable release (#NNN)`

## Steps

### Step 1: Find the latest stable Stripe release

Run: `cd server && uv run python -c "import stripe; print(stripe.__version__)"` to
confirm the current beta version. Then check PyPI for the latest stable 14.x:

```bash
curl -s https://pypi.org/pypi/stripe/json | python3 -c "import sys,json; d=json.load(sys.stdin); print(sorted(d['releases'].keys())[-5:])"
```

Look for the latest `14.x.y` release (no `b`, `rc`, or `a` suffix).

If no stable 14.x is available, STOP and report — the beta may have been the only
release in that series.

### Step 2: Update the version pin

In `server/pyproject.toml`, change:
```
"stripe==14.1.0b1",
```
to:
```
"stripe>=14.1.0,<15",
```
(or pin to the exact stable version found in step 1, e.g., `"stripe==14.2.0"`).

Then sync dependencies:
```bash
cd server && uv sync
```

**Verify**: `cd server && uv run python -c "import stripe; print(stripe.__version__)"` → prints a non-beta version.

### Step 3: Run tests

**Verify**: `cd server && uv run python -m pytest tests/test_stripe.py -v` → all pass.

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

### Step 4: Lint

**Verify**: `cd server && make lint` → exit 0.

## Done criteria

- [ ] `grep "stripe==" server/pyproject.toml` does not contain `b1` or any beta suffix
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] Only `server/pyproject.toml` and `server/uv.lock` modified
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- No stable 14.x release exists on PyPI — report; the beta may be intentional for
  the Financial Connections API.
- Test failures after upgrade that are not caused by this change — report; a
  breaking change in Stripe's API may require updating `stripe.py`.
- The `stripe.api_version = "2022-08-01; financial_connections_transactions_beta=v1"`
  header in `stripe.py:290` is rejected by the new SDK — this beta API version string
  may need updating; report rather than guessing.

## Maintenance notes

- The Financial Connections API was in beta when `stripe==14.1.0b1` was pinned.
  If it has moved to stable, the `api_version` string in `server/resources/stripe.py:290`
  should be updated to remove the `financial_connections_transactions_beta` qualifier.
