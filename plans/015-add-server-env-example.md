# Plan 015: Add server/.env.example for onboarding

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/constants.py CLAUDE.md`
> If either changed, verify the environment variable list before creating the file.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

New developers must read `CLAUDE.md` to find the list of required environment
variables, then create a `.env` file manually. There is no `.env.example` to
copy. The startup validation at `server/application.py:90-92` throws a
`RuntimeError` listing missing variables, but that's a confusing first encounter.
A `.env.example` reduces this to `cp server/.env.example server/.env && edit`.

## Current state

Required environment variables are documented in `CLAUDE.md:193-216` and
enforced at `server/application.py:75-92`. They are sourced from `server/constants.py`.

Read `server/constants.py` to get the exact variable names before creating the file.

No `.env.example` exists at `server/` or the repo root:
`ls server/.env.example` → file not found.

## Commands you will need

| Purpose   | Command                         | Expected on success |
|-----------|---------------------------------|---------------------|
| Verify    | `ls server/.env.example`        | file exists |

## Scope

**In scope**:
- `server/.env.example` (new file to create)

**Out of scope**:
- `CLAUDE.md` — do not change it; it already documents the vars.
- `.gitignore` — `.env` should already be ignored; `.env.example` should NOT be ignored (it's safe to commit). Verify with `cat server/.gitignore` or root `.gitignore`.

## Git workflow

- Branch: `advisor/015-add-server-env-example`
- Commit message style: `Add server/.env.example for environment setup (#NNN)`

## Steps

### Step 1: Read `server/constants.py` to get all variable names

Read `server/constants.py` in full. List every `os.environ.get(...)` or
`os.getenv(...)` call and its default value (if any).

### Step 2: Create `server/.env.example`

Create `server/.env.example` with all environment variables. Use placeholder
values that make the type/format clear without being real credentials:

```bash
# PostgreSQL connection
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USERNAME=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_NAME=budgit
DATABASE_SSL_MODE=prefer

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_COOKIE_DOMAIN=localhost

# Stripe
STRIPE_LIVE_API_SECRET_KEY=sk_live_...
STRIPE_CUSTOMER_ID=cus_...

# Venmo
VENMO_ACCESS_TOKEN=your_venmo_access_token

# Splitwise
SPLITWISE_CONSUMER_KEY=your_key
SPLITWISE_CONSUMER_SECRET=your_secret
SPLITWISE_API_KEY=your_api_key

# Refresh cron protection
SCHEDULED_REFRESH_SECRET=change-me-strong-random-secret

# CORS (comma-separated origins)
CORS_ALLOWED_ORIGINS=http://dev.localhost:5173

# Logging
LOG_LEVEL=INFO
```

Adjust variable names and placeholders to match exactly what `constants.py` reads.

### Step 3: Confirm `.env.example` is not gitignored

**Verify**: `git check-ignore -v server/.env.example` → no output (meaning it is NOT ignored and will be committed).

If it IS ignored, check `.gitignore` and add `!.env.example` to allow it.

### Step 4: Verify the file exists and is valid

**Verify**: `ls server/.env.example` → file exists.

**Verify**: `wc -l server/.env.example` → at least 15 lines.

## Done criteria

- [ ] `server/.env.example` exists and contains all env vars from `constants.py`
- [ ] `git check-ignore -v server/.env.example` returns no output
- [ ] Only `server/.env.example` created (no other files modified)
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- `constants.py` has environment variables not listed in `CLAUDE.md` — add them all.
- `.env` or `.env.example` is not gitignored and would accidentally commit real
  credentials — check `.gitignore` carefully before committing.

## Maintenance notes

- When new environment variables are added to `constants.py`, update `.env.example`
  in the same commit.
- `server/.env.example` should never contain real values — use placeholder strings.
