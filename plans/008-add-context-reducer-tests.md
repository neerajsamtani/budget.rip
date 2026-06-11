# Plan 008: Add tests for toggle and remove reducer actions in LineItemsContext

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- client/src/contexts/LineItemsContext.tsx`
> If it changed, compare the "Current state" excerpts before proceeding.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tests
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

`LineItemsContext.tsx` manages the line items selected by the user in the review
workflow — selection (toggle) and removal (after event creation) are the two
actions that change which items the user sees. The existing test file exercises
`populate_line_items` but does not assert that toggling `isSelected` works or that
`remove_line_items` actually removes items. A regression in the reducer would
leave the UI stuck with items that can't be deselected or removed.

## Current state

`client/src/contexts/LineItemsContext.tsx` — context + reducer.

**Reducer** (`LineItemsContext.tsx:39-65`):
```typescript
case "toggle_line_item_select": {
    return lineItems.map(lineItem => {
        if (lineItem.id === action.lineItemId) {
            return { ...lineItem, isSelected: !lineItem.isSelected };
        } else {
            return lineItem;
        }
    })
}
case "remove_line_items": {
    return lineItems.filter(lineItem => !action.lineItemIds.includes(lineItem.id))
}
```

The test file is at `client/src/contexts/__tests__/LineItemsContext.test.tsx`.
Read it before adding new tests; it defines a `TestComponent` that calls dispatch
actions and a `renderWithProviders` or similar helper.

## Commands you will need

| Purpose   | Command                                                                                      | Expected on success |
|-----------|----------------------------------------------------------------------------------------------|---------------------|
| Tests     | `cd client && npm test -- --testPathPattern="LineItemsContext" --watchAll=false`              | all pass |
| All tests | `cd client && npm test -- --watchAll=false`                                                   | all pass |
| Typecheck | `cd client && npx tsc --noEmit`                                                              | exit 0 |

## Scope

**In scope**:
- `client/src/contexts/__tests__/LineItemsContext.test.tsx`

**Out of scope**:
- `client/src/contexts/LineItemsContext.tsx` — read only.

## Git workflow

- Branch: `advisor/008-add-context-reducer-tests`
- Commit message style: `Add tests for toggle and remove line item actions (#NNN)`

## Steps

### Step 1: Read the existing test file

Read `client/src/contexts/__tests__/LineItemsContext.test.tsx` in full.
Note the existing `TestComponent` structure and how dispatch actions are triggered.

### Step 2: Add three new test cases

Add these test cases to the existing test file, following the same pattern:

**Test 1 — toggle selects an item**:
- Render with two line items, both with `isSelected: false` (or undefined).
- Dispatch `toggle_line_item_select` for item 1's id.
- Assert item 1 in rendered output has `isSelected: true`.
- Assert item 2 is unchanged.

**Test 2 — toggle deselects an already-selected item**:
- Render with one item where `isSelected: true`.
- Dispatch `toggle_line_item_select` for that item's id.
- Assert the item now has `isSelected: false`.

**Test 3 — remove_line_items removes the correct items**:
- Render with three line items.
- Dispatch `remove_line_items` with the ids of items 1 and 3.
- Assert only item 2 remains.
- Assert items 1 and 3 are no longer in the rendered output.

**Verify**: `cd client && npm test -- --testPathPattern="LineItemsContext" --watchAll=false` → all pass, including 3 new tests.

### Step 3: Run all client tests

**Verify**: `cd client && npm test -- --watchAll=false` → all pass.

### Step 4: Typecheck

**Verify**: `cd client && npx tsc --noEmit` → exit 0.

## Done criteria

- [ ] 3 new tests added to `LineItemsContext.test.tsx`
- [ ] Tests cover: toggle→selected, toggle→deselected, remove multiple
- [ ] `cd client && npm test -- --watchAll=false` exits 0
- [ ] Only `client/src/contexts/__tests__/LineItemsContext.test.tsx` modified
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- The existing test file uses a testing pattern incompatible with directly
  dispatching actions (e.g., actions are only triggered via UI interactions) —
  adapt to use the actual UI elements (buttons/clicks) rather than direct dispatch.
- TypeScript errors on the new test cases that can't be fixed without changing
  the context types.

## Maintenance notes

- If `LineItemInterface` gains new fields, the fixture items in these tests may
  need updating.
- The `default` branch in the reducer uses `never` for exhaustive checking; if a
  new action type is added, add a corresponding test.
