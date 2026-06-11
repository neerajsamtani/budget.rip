# Plan 012: Remove unused bootstrap and react-bootstrap dependencies

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- client/package.json`
> If it changed, re-verify the packages are still present and unused before proceeding.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: deps
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

`bootstrap` (5.x) and `react-bootstrap` (2.x) are listed in `client/package.json`
but are never imported anywhere in the source. The Bootstrap → shadcn/ui migration
is complete (noted in `CLAUDE.md`). These packages add ~100KB to install size,
appear in `npm audit` noise, and could cause confusion for developers wondering
whether Bootstrap is in use.

## Current state

`client/package.json:24-25`:
```json
"bootstrap": "^5.2.3",
"react-bootstrap": "^2.6.0",
```

No imports exist anywhere in `client/src/`:
```
grep -r "from 'bootstrap'" client/src/     → 0 matches
grep -r "from 'react-bootstrap'" client/src/ → 0 matches
grep -r "import.*bootstrap" client/src/    → 0 matches
```

## Commands you will need

| Purpose    | Command                                                           | Expected on success |
|------------|-------------------------------------------------------------------|---------------------|
| Pre-check  | `grep -r "bootstrap" client/src/`                                 | 0 matches |
| Uninstall  | `cd client && npm uninstall bootstrap react-bootstrap`            | exit 0 |
| Tests      | `cd client && npm test -- --watchAll=false`                       | all pass |
| Build      | `cd client && npm run build`                                      | exit 0, no errors |
| Typecheck  | `cd client && npx tsc --noEmit`                                   | exit 0 |

## Scope

**In scope**:
- `client/package.json`
- `client/package-lock.json` (updated automatically by npm uninstall)

**Out of scope**:
- Any source file — if grep finds imports, STOP (see conditions below).

## Git workflow

- Branch: `advisor/012-remove-unused-bootstrap`
- Commit message style: `Remove unused bootstrap and react-bootstrap dependencies (#NNN)`

## Steps

### Step 1: Confirm no imports exist

**Verify**: `grep -r "bootstrap" client/src/` → 0 matches.

If any matches are found, STOP — do not uninstall; report the files and lines.

### Step 2: Uninstall the packages

```bash
cd client && npm uninstall bootstrap react-bootstrap
```

**Verify**: `grep '"bootstrap"' client/package.json` → 0 matches.
**Verify**: `grep '"react-bootstrap"' client/package.json` → 0 matches.

### Step 3: Run tests and build

**Verify**: `cd client && npm test -- --watchAll=false` → all pass.

**Verify**: `cd client && npm run build` → exits 0.

**Verify**: `cd client && npx tsc --noEmit` → exits 0.

## Done criteria

- [ ] `grep '"bootstrap"' client/package.json` → 0 matches
- [ ] `grep '"react-bootstrap"' client/package.json` → 0 matches
- [ ] `cd client && npm test -- --watchAll=false` exits 0
- [ ] `cd client && npm run build` exits 0
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- `grep -r "bootstrap" client/src/` returns any matches — Bootstrap may still be
  in use somewhere; report the matches rather than deleting the dependencies.

## Maintenance notes

- After removal, `npm audit` output should be shorter. Any remaining vulnerabilities
  are in other packages.
- If Bootstrap is ever re-added, the shadcn/ui + Tailwind stack is the current
  standard — use those instead.
