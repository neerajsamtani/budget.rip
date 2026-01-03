# Quick Wins for New Contributors

This document lists easy, beginner-friendly tasks that new engineers can tackle to contribute to the codebase and improve it. These "quick wins" help you learn the codebase while making meaningful contributions.

---

## ⭐ Easiest (1-2 hours)

### 1. Fix TypeScript `any` Types in EventHints.tsx

**File**: `client/src/data/EventHints.tsx`
**Lines**: 4, 9, 14, 35

**What to do**: There's a TODO comment asking to remove `any` types. Replace them with proper TypeScript types.

**Current code**:
```typescript
// TODO: Remove "any" types
const getNestedProperty = (obj: any, path: string) => { ... }
const evaluateCondition = (left: any, operator: any, right: any) => { ... }
let rightValue: any = ...
```

**Suggested approach**:
- Create proper type definitions for the CEL evaluator parameters
- Use `LineItemInterface` properties for type safety
- Use string literal types for operators
- Add proper type guards for the `rightValue` conversion

**Skills learned**: TypeScript generics, type narrowing, working with complex types

**Testing**: Ensure existing EventHints tests still pass after changes

---

### 2. Clean Up Unused Splitwise/Venmo Constants

**Files**:
- `server/resources/splitwise.py:26-27`
- `server/resources/venmo.py:27-28`

**What to do**: Investigate whether these constants are still used:
```python
# TODO: Can I remove MOVING_DATE_POSIX
# TODO: Can I remove PARTIES_TO_IGNORE
```

**Approach**:
1. Search the codebase for references to these constants
2. Check git history to understand why they were added
3. If unused, remove them
4. If needed, document why they exist
5. Update tests if necessary

**Skills learned**: Code archaeology, safe refactoring, git history investigation

---

## ⭐⭐ Medium (2-4 hours)

### 3. Create Python Exceptions Module

**Files**: Multiple files in `server/resources/` have `# TODO: Exceptions`
- `server/resources/auth.py:23`
- `server/resources/event.py:26`
- `server/resources/line_item.py:15`
- `server/resources/cash.py:24`
- `server/resources/venmo.py:26`
- `server/resources/splitwise.py:25`
- `server/resources/monthly_breakdown.py:16`

**What to do**: Create a custom exceptions module for better error handling.

**Approach**:
1. Create `server/exceptions.py` with custom exception classes:
   ```python
   class BudgetRipException(Exception):
       """Base exception for Budget.RIP"""
       pass

   class ValidationError(BudgetRipException):
       """Raised when validation fails"""
       pass

   class NotFoundError(BudgetRipException):
       """Raised when a resource is not found"""
       pass

   class AuthorizationError(BudgetRipException):
       """Raised when user is not authorized"""
       pass

   class ExternalAPIError(BudgetRipException):
       """Raised when external API call fails"""
       pass
   ```

2. Update Flask error handlers in `application.py`
3. Replace generic exceptions in resource files
4. Add appropriate HTTP status codes for each exception type

**Skills learned**: Python exception hierarchies, Flask error handling, REST API conventions

**Testing**: Add tests for error scenarios

---

### 4. Extract Reusable Components from CreateEventModal

**File**: `client/src/components/CreateEventModal.tsx`
**Lines**: 145, 164

**What to do**: Extract two reusable components to reduce code duplication.

#### Component 1: CategorySelect (Line 145)
```typescript
// TODO: Is it possible to replace this with a CategoryFilter component?
```

Create a reusable `CategorySelect` component that can be used in multiple places.

#### Component 2: TagsInput (Line 164)
```typescript
// TODO: Create a separate component for adding / removing tags
```

Create a `TagsInput` component for managing tags with add/remove functionality.

**Approach**:
1. Identify the props each component needs
2. Create new component files in `client/src/components/`
3. Write TypeScript interfaces for props
4. Add basic tests for each component
5. Refactor `CreateEventModal` to use the new components

**Skills learned**: React component composition, DRY principles, component API design

**Testing**: Write unit tests for new components

---

### 5. Add Unit Tests for Custom Hooks

**Directory**: `client/src/hooks/`

**What to do**: Many custom React hooks lack dedicated unit tests.

**Approach**:
1. Identify hooks without tests
2. Set up `@testing-library/react-hooks` (if not already installed)
3. Write tests for:
   - Data fetching hooks
   - State management hooks
   - Side effects
4. Mock API calls with MSW

**Example test structure**:
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useEvents } from '../useEvents';

describe('useEvents', () => {
  it('should fetch events successfully', async () => {
    const { result } = renderHook(() => useEvents());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toBeDefined();
  });
});
```

**Skills learned**: Testing custom React hooks, async testing patterns

---

## ⭐⭐⭐ Harder (4-8 hours)

### 6. Optimize Stripe Transaction Fetching

**File**: `server/resources/stripe.py:296`

**What to do**: Currently fetches all transactions ever. Optimize to only fetch new ones.

```python
# TODO: This gets all transactions ever. We should only get those that we don't have
```

**Approach**:
1. Store the timestamp of the last sync in the database (add column to `bank_accounts` table)
2. Add Alembic migration for the new column
3. Use Stripe's `created[gte]` parameter to fetch only transactions after the last sync
4. Update the timestamp after successful sync
5. Add pagination handling for large transaction sets
6. Add error recovery (what if sync fails halfway?)

**Skills learned**:
- API pagination and filtering
- Database migrations with Alembic
- Incremental data sync patterns
- Error handling and recovery

**Testing**:
- Test initial sync (no previous timestamp)
- Test incremental sync
- Test pagination
- Test error scenarios

---

### 7. Implement Stripe Webhook Handler

**File**: `server/application.py:232`

**What to do**: Add webhook endpoint for real-time Stripe updates.

```python
# TODO: Need to add webhooks for updates after the server has started
```

**Approach**:
1. Create new route in `server/resources/stripe.py` for webhooks:
   ```python
   @stripe_bp.route('/webhook', methods=['POST'])
   def stripe_webhook():
       payload = request.data
       sig_header = request.headers.get('Stripe-Signature')

       # Verify webhook signature
       # Process event based on type
       # Update database accordingly
   ```

2. Handle webhook events:
   - `financial_connections.account.created`
   - `financial_connections.account.disconnected`
   - `financial_connections.account.refreshed_balance`

3. Add webhook secret to environment variables
4. Implement idempotency (handle duplicate webhooks)
5. Add logging for webhook events

**Skills learned**:
- Webhooks and event-driven architecture
- Webhook signature verification
- Idempotency patterns
- Stripe API webhooks

**Testing**:
- Use Stripe CLI to test webhooks locally
- Mock webhook payloads in tests
- Test signature verification
- Test idempotency

---

### 8. Upgrade Testing Dependencies

**File**: `.github/workflows/nodejs-client.yml:47`

**What to do**: Remove the workaround for downgrading testing libraries.

```yaml
# TODO: Consider upgrading to react-scripts version 5.x instead of downgrading @testing-library/jest-dom
```

**Approach**:
1. Research compatibility between current React version and testing libraries
2. Create a test branch
3. Remove the downgrade step from CI
4. Upgrade `@testing-library/jest-dom` to latest compatible version
5. Fix any breaking changes in tests
6. Update documentation

**Skills learned**:
- Dependency management
- CI/CD configuration
- Breaking change migration
- SemVer understanding

**Testing**: Ensure all frontend tests pass with new versions

---

## Recommended Starting Order

For new contributors, we recommend tackling tasks in this order:

1. **Start here**: Fix TypeScript `any` types (#1)
   - Low risk, well-scoped
   - Teaches you about the event hints system
   - Good first PR to understand the review process

2. **Second task**: Clean up unused constants (#2)
   - Teaches code archaeology
   - Shows you how to safely remove code
   - Introduces you to git history

3. **Build confidence**: Create exceptions module (#3)
   - More substantial contribution
   - Touches multiple files
   - Teaches backend patterns

4. **Component work**: Extract reusable components (#4)
   - Frontend experience
   - Component design
   - React patterns

5. **Advanced**: Choose from remaining tasks based on interest

---

## Before Starting

1. **Read the code**: Understand the file(s) you'll be modifying
2. **Run the tests**: Make sure everything passes before you start
3. **Create a branch**: Follow the naming convention `claude/your-feature-name-sessionId`
4. **Make small commits**: Commit logical units of work
5. **Write tests**: Add tests for your changes
6. **Update docs**: If you change behavior, update relevant documentation

---

## PR Checklist

Before submitting your PR:

- [ ] Code follows the existing style
- [ ] All tests pass (`make test` for backend, `npm test` for frontend)
- [ ] Linting passes (`make lint` for backend, `npm run lint` for frontend)
- [ ] Added tests for new functionality
- [ ] Updated documentation if needed
- [ ] Removed any debug code or console.logs
- [ ] Commit messages are clear and descriptive

---

## Getting Help

- **Stuck?** Check the [ONBOARDING.md](./ONBOARDING.md) for learning resources
- **Questions?** Ask in your PR or reach out to the team
- **Testing?** See `server/TESTING.md` for testing guidelines

Happy coding! 🚀
