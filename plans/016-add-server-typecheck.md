# Plan 016: Add mypy type checking to the server

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/pyproject.toml server/Makefile`
> If either changed, compare before proceeding.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

The client has `npx tsc --noEmit` as a typecheck gate. The server has no
equivalent. Python type hints exist throughout the codebase (DAO functions,
resource endpoints, utilities) but are never checked — a mismatched return
type or wrong argument goes undetected until a runtime error. Adding mypy
with a `make typecheck` target gives the same fast feedback loop the client has.

## Current state

`server/pyproject.toml` — no mypy configuration or dev dependency.
`server/Makefile` — defines `lint`, `test`, `test-coverage`, etc. No `typecheck` target.

The codebase uses `Optional`, `Dict`, `List`, `Any` from `typing` throughout,
so mypy will have material to check.

## Commands you will need

| Purpose    | Command                                    | Expected on success |
|------------|--------------------------------------------|---------------------|
| Install    | `cd server && uv sync`                     | exit 0 |
| Typecheck  | `cd server && make typecheck`              | exit 0 |
| Tests      | `cd server && uv run python -m pytest -v`  | all pass |

## Scope

**In scope**:
- `server/pyproject.toml` — add mypy dev dependency and `[tool.mypy]` config
- `server/Makefile` — add `typecheck` target

**Out of scope**:
- Fixing all existing type errors — the goal is to establish the baseline;
  errors in existing code are addressed by setting `ignore_errors = True` per
  module or using `# type: ignore` sparingly. A clean bill of health is a
  follow-up task.
- `server/alembic/` and `server/migrations/` — exclude these from mypy.

## Git workflow

- Branch: `advisor/016-add-server-typecheck`
- Commit message style: `Add mypy type checking to server (#NNN)`

## Steps

### Step 1: Add mypy to dev dependencies

In `server/pyproject.toml`, under `[dependency-groups] dev`, add:
```toml
"mypy>=1.13.0",
"types-requests>=2.32.0",
```

Then sync:
```bash
cd server && uv sync
```

**Verify**: `cd server && uv run mypy --version` → prints `mypy X.Y.Z`.

### Step 2: Add mypy configuration to pyproject.toml

Add a `[tool.mypy]` section to `server/pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"
ignore_missing_imports = true
exclude = [
    "alembic/",
    "migrations/",
    "tests/",
]
```

`ignore_missing_imports = true` handles third-party libs without stubs (Stripe, Splitwise, etc.)
without requiring stub packages for every dependency.

### Step 3: Do a first run and capture errors

```bash
cd server && uv run mypy . 2>&1 | tail -20
```

If there are errors in the application code (not test/alembic), add per-file
ignores for existing violations rather than fixing them all:

```toml
[tool.mypy]
...
[[tool.mypy.overrides]]
module = ["resources.*", "utils.*"]
ignore_errors = true
```

The goal is a passing `mypy` run, not zero errors in existing code. Fixing
existing errors is a separate task.

### Step 4: Add Makefile target

In `server/Makefile`, add after the existing `lint` target:

```makefile
typecheck:
	uv run mypy .
```

Match the indentation style (tabs) used by the existing targets.

**Verify**: `cd server && make typecheck` → exits 0.

### Step 5: Confirm tests still pass

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

## Done criteria

- [ ] `cd server && make typecheck` exits 0
- [ ] `mypy` is listed in `[dependency-groups] dev` in `pyproject.toml`
- [ ] `[tool.mypy]` section exists in `pyproject.toml`
- [ ] `make typecheck` target exists in `Makefile`
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] Only `server/pyproject.toml`, `server/uv.lock`, `server/Makefile` modified
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- mypy produces hundreds of errors in core files that make `make typecheck` unusable
  even with `ignore_errors = true` on specific modules — add a global
  `follow_imports = "silent"` instead and report.

## Maintenance notes

- New code added to the server should pass mypy without needing `# type: ignore`.
  The `ignore_errors = true` overrides are technical debt to clean up incrementally.
- Once errors are fixed file by file, remove the per-file ignores from
  `pyproject.toml` to enforce type safety progressively.
