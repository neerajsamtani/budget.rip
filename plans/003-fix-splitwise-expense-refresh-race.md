# Plan 003: Await Splitwise refresh before invalidating line items cache

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- client/src/hooks/useApi.ts`
> If `useApi.ts` changed, compare the "Current state" excerpt before proceeding.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

When a user creates a Splitwise expense, the mutation fires a background refresh
of the Splitwise account to import the new expense as a line item. The refresh
is fire-and-forget (`.then()` but the promise is `void`-ed), so the `lineItems`
query is invalidated immediately after the mutation — before the server has
finished importing the new expense. The user sees success toast but the new
expense may not appear in the list until the next manual refresh.

## Current state

`client/src/hooks/useApi.ts` — all TanStack Query API hooks.

**Bug site** (`client/src/hooks/useApi.ts:268-275`):
```typescript
onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['connectedAccounts'] });
    void axiosInstance
        .post('api/refresh/account', { accountId: 'splitwise', source: 'splitwise' })
        .then(() => queryClient.invalidateQueries({ queryKey: ['lineItems'] }))
        .catch((error) => console.error('Failed to refresh Splitwise after expense creation', error));
},
```

`void axiosInstance.post(...)` starts the refresh request but doesn't await it.
The `.then()` callback invalidates `lineItems` after the POST resolves, but
because it's `void`-ed the `onSuccess` handler returns immediately and the
`connectedAccounts` invalidation fires while the refresh is still running.

**Fix pattern**: The `mutationFn` in `useCreateManualTransaction` (lines 245-250)
shows the correct pattern — `async/await` with `axiosInstance.post`.

**The correct behavior**: `onSuccess` should `await` the refresh POST, then
invalidate `lineItems`. The `connectedAccounts` invalidation can happen immediately
(no ordering dependency).

## Commands you will need

| Purpose   | Command                                                               | Expected on success |
|-----------|-----------------------------------------------------------------------|---------------------|
| Typecheck | `cd client && npx tsc --noEmit`                                       | exit 0, no errors |
| Tests     | `cd client && npm test -- --testPathPattern="useApi" --watchAll=false` | all pass |
| All tests | `cd client && npm run test -- --watchAll=false`                        | all pass |
| Lint      | `cd client && npm run lint` (if script exists) or check `package.json` | exit 0 |

## Scope

**In scope**:
- `client/src/hooks/useApi.ts` (the `onSuccess` in `useCreateSplitwiseExpense`)

**Out of scope**:
- Server-side refresh logic.
- Other mutation hooks.

## Git workflow

- Branch: `advisor/003-fix-splitwise-refresh-race`
- Commit message style: `Await Splitwise refresh before invalidating line items cache (#NNN)`

## Steps

### Step 1: Convert the `onSuccess` to async/await

In `client/src/hooks/useApi.ts`, find the `useCreateSplitwiseExpense` hook
(around line 260). Replace the current `onSuccess` with:

```typescript
onSuccess: async () => {
    queryClient.invalidateQueries({ queryKey: ['connectedAccounts'] });
    try {
        await axiosInstance.post('api/refresh/account', { accountId: 'splitwise', source: 'splitwise' });
        queryClient.invalidateQueries({ queryKey: ['lineItems'] });
    } catch (error) {
        console.error('Failed to refresh Splitwise after expense creation', error);
    }
},
```

Key changes:
- `onSuccess` is now `async`.
- The `void` prefix is removed; `await` waits for the POST before invalidating.
- The `.then()` chain is replaced with `await` + `try/catch`.

**Verify**: `grep -A 12 "useCreateSplitwiseExpense" client/src/hooks/useApi.ts | grep "async"` → matches `async () => {`.

### Step 2: Typecheck

**Verify**: `cd client && npx tsc --noEmit` → exit 0.

### Step 3: Run tests

**Verify**: `cd client && npm test -- --testPathPattern="useApi" --watchAll=false` → all pass.

## Test plan

In `client/src/hooks/__tests__/useApi.test.tsx`, add a test for
`useCreateSplitwiseExpense` verifying that `lineItems` is only invalidated
after the refresh POST resolves. Use MSW to mock both
`POST api/splitwise/expenses` (mutation) and `POST api/refresh/account`
(refresh). Assert that `invalidateQueries` for `['lineItems']` is called
**after** the refresh POST, not before.

Use the existing test file structure as the pattern.

**Verify**: `cd client && npm test -- --testPathPattern="useApi" --watchAll=false` → all pass including new test.

## Done criteria

- [ ] `grep "void axiosInstance" client/src/hooks/useApi.ts` returns no matches
- [ ] `cd client && npx tsc --noEmit` exits 0
- [ ] `cd client && npm test -- --watchAll=false` exits 0
- [ ] Only `client/src/hooks/useApi.ts` and its test file modified
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- The `useCreateSplitwiseExpense` hook has been significantly refactored and no
  longer matches the "Current state" excerpt.
- TypeScript errors after the change that suggest the `onSuccess` async signature
  is not compatible with the TanStack Query `UseMutationOptions` type — report.

## Maintenance notes

- TanStack Query v5 `onSuccess` callbacks support `async` — no library upgrade needed.
- If the Splitwise refresh endpoint ever becomes a long-running job (fires a background
  task and returns immediately), this approach needs revisiting — the `await` would
  only wait for the job to be *queued*, not completed. In that case, polling or a
  websocket notification would be needed.
