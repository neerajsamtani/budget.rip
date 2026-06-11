# Plan 024: Fix stale documentation in CLAUDE.md and client README

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- CLAUDE.md client/README.md`
> If either changed, re-read before proceeding.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: docs
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

Two documentation files are actively wrong:

1. `CLAUDE.md:142` states "Legacy collection names defined as string constants in
   `dao.py` for backwards compatibility" — the MongoDB migration is complete, no
   such code exists. New developers waste time looking for it.

2. `client/README.md` contains setup instructions using `pip3 install`, `FLASK_APP=server.py`,
   and CRA patterns that fail completely with the current stack (uv, Vite, `dev.localhost`).
   The bottom half is a TODO list, not documentation.

## Current state

**CLAUDE.md** — line 142 (in the "Server (Python/Flask)" conventions section):
```
- Legacy collection names defined as string constants in `dao.py` for backwards compatibility
```

Verified: `grep -n "collection" server/dao.py` → only `from collections import defaultdict` (standard library, unrelated).

**client/README.md** lines 1-35 — setup instructions that reference `pip3 install`,
`export FLASK_APP=server.py`, `python3 -m flask run --port=4242`, and
`npm start` without mentioning `dev.localhost:5173` or Vite. Lines 40-66 are
a raw TODO list (`### Deploy Online`, `### Fix Leaky Abstraction`).

## Commands you will need

No build commands needed for documentation changes.

**Verify completeness**: `grep "Legacy collection\|legacy collection" CLAUDE.md` → 0 matches after fix.

## Scope

**In scope**:
- `CLAUDE.md` — remove line 142 only
- `client/README.md` — rewrite with accurate quick-start

**Out of scope**:
- `server/MONGODB_TO_POSTGRES_MIGRATION.md` — historical document, do not change.
- Any code files.

## Git workflow

- Branch: `advisor/024-update-stale-docs`
- Commit message style: `Fix stale documentation in CLAUDE.md and client README (#NNN)`

## Steps

### Step 1: Remove stale line from CLAUDE.md

Find the line "Legacy collection names defined as string constants in `dao.py`
for backwards compatibility" and remove it. The surrounding bullet list in the
"Server (Python/Flask)" conventions section should remain intact.

**Verify**: `grep "Legacy collection\|legacy collection" CLAUDE.md` → 0 matches.

### Step 2: Rewrite client/README.md

Replace `client/README.md` with a minimal accurate quick-start:

```markdown
# Budget Client

React 18 + TypeScript + Vite frontend for budget.rip.

## Quick Start

1. Ensure Node.js v22 is active: `nvm use 22`
2. Install dependencies: `npm install`
3. Start the dev server: `npm start` (runs at http://dev.localhost:5173)

For full development setup, environment variables, and architecture documentation,
see [CLAUDE.md](../CLAUDE.md) in the repo root.

## Commands

| Command              | Description                          |
|----------------------|--------------------------------------|
| `npm start`          | Start dev server on dev.localhost    |
| `npm run build`      | Production build                     |
| `npm test`           | Run all tests once                   |
| `npm run test:watch` | Run tests in watch mode              |
| `npm run analyze`    | Visualize bundle size                |
```

Do NOT preserve the TODO list from the old README — it belongs in GitHub Issues
or a roadmap document, not in README.

### Step 3: Verify no accidental changes

**Verify**: `git diff --stat` → only `CLAUDE.md` and `client/README.md` modified.

## Done criteria

- [ ] `grep "Legacy collection" CLAUDE.md` → 0 matches
- [ ] `client/README.md` setup instructions reflect the current stack (npm, Vite, dev.localhost)
- [ ] `client/README.md` does not contain TODO list items
- [ ] Only `CLAUDE.md` and `client/README.md` modified
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- `CLAUDE.md` line 142 contains content beyond the legacy MongoDB reference (the
  whole line is a list item — removing it should not break the list structure).
  Check the surrounding lines before deleting.

## Maintenance notes

- `CLAUDE.md` is the authoritative source of truth for the stack. When
  `client/README.md` diverges from `CLAUDE.md`, `CLAUDE.md` wins.
- If more stale sections are found in `CLAUDE.md` while making this change,
  fix them in the same commit and note them in the commit message.
