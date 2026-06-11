# Plan 020: Add structured exception handling across resource blueprints

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/resources/venmo.py server/resources/splitwise.py server/resources/event.py server/resources/line_item.py server/resources/auth.py server/resources/monthly_breakdown.py`
> If any in-scope file changed significantly, compare before proceeding.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MED
- **Depends on**: 005 (exception detail leak fix should land first)
- **Category**: tech-debt
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

Six resource files have a `# TODO: Exceptions` comment at the top because their
refresh/transform functions lack structured exception handling. When an external
API (Venmo, Splitwise) fails, the exception propagates to Flask's global handler
(`application.py:145`), which returns a generic 500. This is fine for the client,
but the server logs a confusing traceback instead of a structured error message.

More importantly, the refresh endpoints (`/api/refresh_*`) are called both by
users clicking "Refresh" and by the scheduled cron job. A partial failure (one
source fails) should log clearly and allow the overall refresh to continue, not
blow up the whole operation.

This plan wraps the core integration functions with try/except and logs structured
errors, without changing the API contract.

## Current state

Each resource file has a `# TODO: Exceptions` marker at the top:
- `server/resources/venmo.py:21`
- `server/resources/splitwise.py:39`
- `server/resources/event.py:20`
- `server/resources/line_item.py:15`
- `server/resources/auth.py:24`
- `server/resources/monthly_breakdown.py:16`

Read each file to understand which functions lack try/except and what exceptions
could realistically occur (network errors, API auth failures, DB errors).

The global handler (`server/application.py:145-151`) already handles uncaught
exceptions with a generic 500 — this plan adds *specific* handling for anticipated
failures in resource functions.

## Commands you will need

| Purpose   | Command                                 | Expected on success |
|-----------|-----------------------------------------|---------------------|
| Tests     | `cd server && uv run python -m pytest -v` | all pass |
| Lint      | `cd server && make lint`                | exit 0 |

## Scope

**In scope**:
- `server/resources/venmo.py`
- `server/resources/splitwise.py`
- `server/resources/event.py`
- `server/resources/line_item.py`
- `server/resources/auth.py`
- `server/resources/monthly_breakdown.py`

**Out of scope**:
- `server/resources/stripe.py` — plan 005 already addressed Stripe's exception handling.
- `server/application.py` — the global handler is correct; do not touch it.
- Creating a custom exception class hierarchy — this plan uses Python's standard
  exceptions and clear log messages.

## Git workflow

- Branch: `advisor/020-add-exception-handling`
- Commit message style: `Add structured exception handling to resource blueprints (#NNN)`

## Steps

### Step 1: Read each in-scope resource file

Read all 6 files in full. For each one, identify:
- Which endpoints are "safe" (DB reads only, unlikely to fail) vs "risky" (external API calls).
- Which functions are already wrapped in try/except.
- What the `# TODO: Exceptions` comment was intended to address.

### Step 2: Wrap external API calls in resource functions

For each refresh/ingest endpoint that calls an external API (Venmo, Splitwise):

```python
@venmo_blueprint.route("/api/refresh/venmo", methods=["POST"])
@jwt_required()
def refresh_venmo_api():
    try:
        refresh_venmo()
        return jsonify({"message": "Refreshed Venmo data"}), 200
    except Exception as e:
        logger.error(f"Venmo refresh failed: {e}", exc_info=True)
        return jsonify({"error": "Venmo refresh failed"}), 500
```

The key elements:
- `logger.error(f"...: {e}", exc_info=True)` captures the full traceback in logs.
- Response to client: generic message (plan 005 already established this pattern).
- Do NOT swallow exceptions silently (no empty except blocks).

### Step 3: Remove `# TODO: Exceptions` comments

After adding proper exception handling to a file, remove the `# TODO: Exceptions`
comment at the top of that file.

**Verify**: `grep -rn "TODO: Exceptions" server/resources/` → 0 matches.

### Step 4: Run tests

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

### Step 5: Lint

**Verify**: `cd server && make lint` → exit 0.

## Done criteria

- [ ] `grep -rn "# TODO: Exceptions" server/resources/` → 0 matches
- [ ] All 6 in-scope resource files have try/except around external API calls
- [ ] `logger.error(..., exc_info=True)` is used in each except block
- [ ] No silent exception swallowing (no `except Exception: pass`)
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- A resource file's function is already wrapped in try/except — note it and skip;
  do not add redundant nested try/except.
- An endpoint needs to return specific error codes based on exception type
  (e.g., 401 for auth failures vs 503 for network errors) — implement that
  distinction rather than a blanket 500.

## Maintenance notes

- New external API integration files should always wrap external calls in
  try/except with `logger.error(..., exc_info=True)` from the start.
- The scheduled refresh (`/api/refresh/scheduled` in `application.py`) calls
  `refresh_all()` which calls each integration's refresh function. With this
  plan, each function handles its own errors — `refresh_all()` should log but
  continue if one source fails rather than aborting the whole refresh. Check
  `helpers.py` or wherever `refresh_all` is defined to verify this behavior.
