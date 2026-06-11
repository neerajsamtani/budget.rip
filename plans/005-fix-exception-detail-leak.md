# Plan 005: Replace raw exception messages with generic client errors

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/resources/stripe.py server/resources/event.py`
> If either file changed, compare the "Current state" excerpts before proceeding.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

Seven catch blocks return `jsonify(error=str(e)), 500`, sending raw Python
exception messages to the client. These messages can contain internal API details
(e.g., Stripe SDK error messages with account IDs, connection strings, rate-limit
headers). A global error handler at `server/application.py:145-151` already returns
a generic "Internal server error" for unhandled exceptions and logs the full
traceback. The explicit `str(e)` returns in resource files bypass that handler,
leaking information the handler was designed to suppress.

## Current state

All 7 sites return `jsonify(error=str(e)), 500`:

```
server/resources/stripe.py:165    create_fc_session_api
server/resources/stripe.py:193    get_accounts_api
server/resources/stripe.py:245    subscribe_to_account_api
server/resources/stripe.py:264    reactivate_account_api
server/resources/stripe.py:280    refresh_account_api
server/resources/stripe.py:331    refresh_transactions_api
server/resources/event.py:205     (look for the try/except block)
```

**Existing correct pattern** (`server/application.py:145-151`):
```python
@application.errorhandler(Exception)
def handle_unexpected_error(err):
    if isinstance(err, HTTPException):
        return err.get_response()
    logger.exception("Unhandled exception", exc_info=err)
    return jsonify({"error": "Internal server error"}), 500
```

The fix: keep `logger.error` / `logger.exception` (already present at each site),
replace `str(e)` in the response with a generic message.

## Commands you will need

| Purpose   | Command                             | Expected on success |
|-----------|-------------------------------------|---------------------|
| Tests     | `cd server && uv run python -m pytest tests/test_stripe.py tests/test_event.py -v` | all pass |
| All tests | `cd server && uv run python -m pytest -v` | all pass |
| Lint      | `cd server && make lint`            | exit 0 |

## Scope

**In scope**:
- `server/resources/stripe.py` (6 sites)
- `server/resources/event.py` (1 site)

**Out of scope**:
- `server/application.py` — the global handler is correct, leave it.
- Any other resource file — check for `jsonify(error=str(e))` there too:
  `grep -rn 'jsonify(error=str(e))' server/resources/` and if any additional
  matches appear beyond the 7 listed, apply the same fix.

## Git workflow

- Branch: `advisor/005-fix-exception-detail-leak`
- Commit message style: `Return generic error messages instead of exception details (#NNN)`

## Steps

### Step 1: Confirm all 7 sites

**Verify**: `grep -rn 'jsonify(error=str(e))' server/resources/` → exactly 7 matches.

If you see a different count, fix ALL matches found (add any extras, skip any listed
here that are absent) and proceed.

### Step 2: Replace all `str(e)` in error responses

For each of the 7 sites, the pattern is:
```python
    except Exception as e:
        return jsonify(error=str(e)), 500
```

Change to:
```python
    except Exception as e:
        logger.error(f"<descriptive context>: {e}")
        return jsonify({"error": "Request failed"}), 500
```

Where `<descriptive context>` is the function name or a short description of what
failed (e.g., `"Error creating financial connections session"`,
`"Error refreshing transactions"`). If a `logger.error` call already exists in the
except block, keep it and just change the `jsonify` line.

**Note on event.py:205**: look at the full except block there. If the exception
variable is not `e`, adjust accordingly.

**Verify after each file**: `grep -n 'jsonify(error=str' server/resources/stripe.py` → 0 matches.

**Verify**: `grep -rn 'jsonify(error=str(e))' server/resources/` → 0 matches.

### Step 3: Run tests

**Verify**: `cd server && uv run python -m pytest tests/test_stripe.py tests/test_event.py -v` → all pass.

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

### Step 4: Lint

**Verify**: `cd server && make lint` → exit 0.

## Test plan

No new tests required — the existing tests cover the success paths. The change is
purely to the error response body, which isn't tested by current tests.

If you want to add a test: in `test_stripe.py`, mock a Stripe API call to raise
an exception and assert the response body contains `{"error": "Request failed"}`
and not any substring of the exception message.

## Done criteria

- [ ] `grep -rn 'jsonify(error=str(e))' server/resources/` returns 0 matches
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] Only `server/resources/stripe.py` and `server/resources/event.py` modified
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- More than 7 matches found in step 1 — fix all of them, document the extras.
- A match is in a function where the exception contains user-meaningful detail
  the client needs (e.g., validation errors) — those should return 400, not 500;
  report rather than blindly converting to generic 500.

## Maintenance notes

- The global handler in `application.py:145` already handles unhandled exceptions
  generically. The explicit `except Exception as e:` blocks in resource files
  exist to log context-specific details; the fix ensures they log but don't expose.
- If a resource ever needs to return structured error information about a specific
  failure mode to the client (e.g., "Stripe account not found"), use an explicit
  `return jsonify({"error": "Account not found"}), 404` with a specific status code,
  not `str(e)`.
