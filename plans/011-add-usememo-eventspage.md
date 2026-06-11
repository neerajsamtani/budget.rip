# Plan 011: Memoize spending calculations in EventsPage

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- client/src/pages/EventsPage.tsx`
> If it changed, compare the "Current state" excerpts before proceeding.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

`EventsPage` calculates `cashFlowWithFilters`, `spending`, and `filteredEvents`
on every render by iterating the full events array. With hundreds of events and
fast filter interactions (category, month, tag), these three iterations run
redundantly on renders triggered by unrelated state changes. `useMemo` pins them
to their actual dependencies.

## Current state

`client/src/pages/EventsPage.tsx` — events list page.

**Calculations run on every render** (`EventsPage.tsx:44-73`):
```typescript
const matchCategory = (event: EventInterface) => category === "All" || category === event.category
const matchTags = (event: EventInterface) => { ... }
const calculateSpending = (events: EventInterface[]) => { ... }
const calculateCashFlowWithFilters = (events: EventInterface[]) => { ... }

const cashFlowWithFilters = calculateCashFlowWithFilters(events);  // iterates all
const spending = calculateSpending(events);                         // iterates all
const filteredEvents = events.filter(event => matchCategory(event) && matchTags(event));
```

`matchCategory` and `matchTags` depend on `category`, `tagFilter`, `events`.
`calculateSpending` and `calculateCashFlowWithFilters` also depend on those.
`filteredEvents` depends on all three.

**Pattern to follow**: `client/src/pages/GraphsPage.tsx` already uses `useMemo`
for similar filtering — use it as the exemplar.

## Commands you will need

| Purpose   | Command                                                                     | Expected on success |
|-----------|-----------------------------------------------------------------------------|---------------------|
| Typecheck | `cd client && npx tsc --noEmit`                                             | exit 0 |
| Tests     | `cd client && npm test -- --testPathPattern="EventsPage" --watchAll=false`  | all pass |
| All tests | `cd client && npm test -- --watchAll=false`                                  | all pass |

## Scope

**In scope**:
- `client/src/pages/EventsPage.tsx`

**Out of scope**:
- `client/src/pages/GraphsPage.tsx` — already has memoization; do not change.
- Any component imported by EventsPage.

## Git workflow

- Branch: `advisor/011-usememo-eventspage`
- Commit message style: `Memoize EventsPage spending calculations (#NNN)`

## Steps

### Step 1: Verify `useMemo` is already imported

Check the import at the top of `EventsPage.tsx`. `useMemo` should be in the
React import. If `useState` is imported as `import React, { useState } from 'react'`,
add `useMemo` to the destructure.

**Verify**: `grep "useMemo" client/src/pages/EventsPage.tsx` → 1 match in the import.

### Step 2: Wrap `filteredEvents`, `spending`, and `cashFlowWithFilters` in `useMemo`

Replace:
```typescript
const cashFlowWithFilters = calculateCashFlowWithFilters(events);
const spending = calculateSpending(events);
const filteredEvents = events.filter(event => matchCategory(event) && matchTags(event));
```

With:
```typescript
const filteredEvents = useMemo(
    () => events.filter(event => matchCategory(event) && matchTags(event)),
    [events, category, tagFilter]
);
const spending = useMemo(
    () => calculateSpending(events),
    [events, category, tagFilter]
);
const cashFlowWithFilters = useMemo(
    () => calculateCashFlowWithFilters(events),
    [events, category, tagFilter]
);
```

Note: `matchCategory` and `matchTags` are defined in the same component body
and close over `category` and `tagFilter`. Rather than adding them to the
dependency array as unstable function references, list their actual dependencies
(`category`, `tagFilter`) directly.

**Verify**: `cd client && npx tsc --noEmit` → exit 0.

### Step 3: Run tests

**Verify**: `cd client && npm test -- --testPathPattern="EventsPage" --watchAll=false` → all pass.

**Verify**: `cd client && npm test -- --watchAll=false` → all pass.

## Done criteria

- [ ] `cashFlowWithFilters`, `spending`, and `filteredEvents` are wrapped in `useMemo`
- [ ] `cd client && npx tsc --noEmit` exits 0
- [ ] `cd client && npm test -- --watchAll=false` exits 0
- [ ] Only `client/src/pages/EventsPage.tsx` modified
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- TypeScript errors because `matchCategory` or `matchTags` appear in dependency
  arrays as unstable function references — extract them out of the component or
  use `useCallback`, and report the approach taken.

## Maintenance notes

- If new filter state variables are added to `EventsPage`, add them to the
  `useMemo` dependency arrays.
- `calculateSpending` and `calculateCashFlowWithFilters` are defined inside the
  component — a future cleanup could move them outside and pass filters as arguments,
  eliminating the closure dependency issue entirely.
