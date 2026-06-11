# Plan 014: Upgrade @testing-library packages to current major versions

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- client/package.json`
> If it changed, verify the versions before proceeding.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: deps
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

`@testing-library/react` is at `^13.4.0` (current: 15.x) and
`@testing-library/user-event` is at `^13.5.0` (current: 14.x). The CI workflow
explicitly downgrades `@testing-library/jest-dom` to 5.16.5 for compatibility.
Two major-version gaps means missing bug fixes, API improvements, and increased
friction as the rest of the ecosystem advances. The CI workaround is a sign the
version debt is already causing pain.

## Current state

`client/package.json` (relevant lines):
```json
"@testing-library/react": "^13.4.0",
"@testing-library/user-event": "^13.5.0",
"@testing-library/jest-dom": "^5.16.5",
```

CI workaround (look for it in `.github/workflows/nodejs-client.yml`) explicitly
installs an older `jest-dom` version.

## Commands you will need

| Purpose    | Command                                                           | Expected on success |
|------------|-------------------------------------------------------------------|---------------------|
| Tests      | `cd client && npm test -- --watchAll=false`                       | all pass |
| Typecheck  | `cd client && npx tsc --noEmit`                                   | exit 0 |

## Scope

**In scope**:
- `client/package.json`
- `client/package-lock.json`
- Any test file that needs updating for breaking API changes
- `.github/workflows/nodejs-client.yml` — remove the jest-dom workaround if it
  becomes unnecessary

**Out of scope**:
- Production source files — no changes to `src/` outside of `__tests__/` dirs.

## Git workflow

- Branch: `advisor/014-upgrade-testing-library`
- Commit message style: `Upgrade @testing-library packages to current versions (#NNN)`

## Steps

### Step 1: Check current latest versions

```bash
cd client && npm info @testing-library/react version
npm info @testing-library/user-event version
npm info @testing-library/jest-dom version
```

Note the latest stable versions for each.

### Step 2: Upgrade packages

```bash
cd client && npm install \
  @testing-library/react@latest \
  @testing-library/user-event@latest \
  @testing-library/jest-dom@latest
```

### Step 3: Run tests — expect some failures

```bash
cd client && npm test -- --watchAll=false 2>&1 | head -80
```

Common breaking changes between major versions:
- `@testing-library/user-event` v14: `userEvent.setup()` is now required instead
  of direct `userEvent.click()` etc. Update test calls from `userEvent.click(el)`
  to `const user = userEvent.setup(); await user.click(el)`.
- `@testing-library/react` v14/v15: `render` and `act` APIs may have minor changes.
  Check the migration guide at https://testing-library.com/docs/react-testing-library/migrate-from-v13.

Fix all failing tests. For each fix, match the style of the surrounding test code.

### Step 4: Remove CI jest-dom workaround

Read `.github/workflows/nodejs-client.yml`. If it contains a step that downgrades
`@testing-library/jest-dom` or runs `npm install @testing-library/jest-dom@5.x`,
remove that step (it's no longer needed after the upgrade).

### Step 5: Final verification

**Verify**: `cd client && npm test -- --watchAll=false` → all pass.

**Verify**: `cd client && npx tsc --noEmit` → exit 0.

## Done criteria

- [ ] `@testing-library/react`, `user-event`, and `jest-dom` in package.json are at current major versions
- [ ] CI workaround for jest-dom removed (if present)
- [ ] `cd client && npm test -- --watchAll=false` exits 0, all existing tests pass
- [ ] `cd client && npx tsc --noEmit` exits 0
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- More than ~10 test files fail after upgrade — the migration surface is larger
  than expected; report the failure list before attempting fixes.
- `userEvent` API changes require restructuring test logic (not just wrapping
  in `userEvent.setup()`) — report rather than guessing the correct approach.

## Maintenance notes

- After this upgrade, test code should use `const user = userEvent.setup(); await user.click(...)`.
  Document this in a comment in `client/src/setupTests.ts` if helpful.
- Future upgrades: pin to a `^` range rather than a specific version to receive
  patch updates automatically.
