# Plan 017: Add pre-commit hooks for linting

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `ls .pre-commit-config.yaml 2>/dev/null && echo exists || echo absent`
> If it already exists, STOP — this plan is already done or superseded.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

Lint violations (ruff, ESLint) are currently caught only in CI or by manually
running `make lint`. Pre-commit hooks catch them before the commit is made,
preventing a commit→push→CI-fail→fix cycle for trivial formatting issues.
For a single developer, this is a quality-of-life improvement that takes
minutes to set up.

## Current state

No `.pre-commit-config.yaml` at the repo root. `server/Makefile` has `make lint`
(runs ruff). Client has ESLint configured.

## Commands you will need

| Purpose        | Command                                               | Expected on success |
|----------------|-------------------------------------------------------|---------------------|
| Install hook   | `pre-commit install`                                  | hook installed |
| Test all files | `pre-commit run --all-files`                          | all pass |
| Tests (server) | `cd server && uv run python -m pytest -v`             | all pass |

Note: `pre-commit` must be installed in the environment. Check with
`pre-commit --version`. If absent, install it: `pip install pre-commit` or
`uv tool install pre-commit`.

## Scope

**In scope**:
- `.pre-commit-config.yaml` (new file at repo root)

**Out of scope**:
- `server/Makefile` — do not modify.
- CI workflow files — pre-commit is for local use; CI already runs linting separately.

## Git workflow

- Branch: `advisor/017-add-precommit-hooks`
- Commit message style: `Add pre-commit hooks for ruff and trailing whitespace (#NNN)`

## Steps

### Step 1: Create `.pre-commit-config.yaml`

Create at the repo root:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.5   # match ruff version in server/pyproject.toml dev deps
    hooks:
      - id: ruff
        args: [--fix]
        files: ^server/
      - id: ruff-format
        files: ^server/

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
```

Check `server/pyproject.toml [dependency-groups] dev` for the exact ruff version
(`ruff>=X.Y.Z`) and use a matching `rev` tag from the ruff-pre-commit repo.
Find the correct tag at: https://github.com/astral-sh/ruff-pre-commit/releases

### Step 2: Install the hooks

```bash
pre-commit install
```

**Verify**: `cat .git/hooks/pre-commit` → file exists and references pre-commit.

### Step 3: Test against all files

```bash
pre-commit run --all-files
```

If ruff finds violations in existing code and auto-fixes them, commit those fixes.
If ruff cannot auto-fix some violations, investigate and fix manually or add
`--exit-zero` to the ruff args for the initial pass (document why).

**Verify**: `pre-commit run --all-files` → exits 0.

### Step 4: Confirm no test regressions

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

## Done criteria

- [ ] `.pre-commit-config.yaml` exists at the repo root
- [ ] `pre-commit install` has been run (`.git/hooks/pre-commit` exists)
- [ ] `pre-commit run --all-files` exits 0
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] Only `.pre-commit-config.yaml` created (plus any auto-fixed lint violations)
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- `pre-commit` is not available and cannot be installed in the current environment —
  report; this plan requires the tool.
- `pre-commit run --all-files` finds violations in many files that cannot be
  auto-fixed — fix them separately before enabling the hook.

## Maintenance notes

- When the ruff version in `pyproject.toml` is upgraded, update the `rev` in
  `.pre-commit-config.yaml` to match.
- ESLint pre-commit hook was omitted intentionally: ESLint requires `node_modules`
  to be installed, which makes the hook slow for server-only commits. Add it only
  if the pain of missing ESLint pre-commit catches becomes significant.
