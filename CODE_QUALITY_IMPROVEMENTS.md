# Code Quality Improvement TODOs

This document tracks code quality improvements for the Budget.rip codebase. All improvements maintain existing functionality while improving readability, maintainability, and robustness.

**Status:** Generated from codebase analysis
**Last Updated:** 2025-11-26

---

## Priority Order

1. [Configuration & Constants](#1-configuration--constants) - Security & Portability
2. [Error Handling Consistency](#2-error-handling-consistency) - User Experience
3. [Type Safety](#3-type-safety) - Bug Prevention
4. [Code Duplication](#4-code-duplication) - Maintenance
5. [Database Session Management](#5-database-session-management) - Resource Management
6. [TODO Comment Cleanup](#6-todo-comment-cleanup) - Quick Wins
7. [Documentation](#7-documentation) - Long-term Maintenance
8. [Logging Improvements](#8-logging-improvements) - Debugging
9. [Magic Strings & Numbers](#9-magic-strings--numbers) - Code Quality
10. [Component Organization](#10-component-organization) - Frontend Architecture

---

## 1. Configuration & Constants

**Priority:** HIGH (Security & Portability)
**Impact:** Makes app usable by other users, improves security

### Issues

- [ ] Hard-coded personal data in `server/constants.py`:
  - `GATED_USERS = ["neerajjsamtani@gmail.com"]` (line 20)
  - `USER_FIRST_NAME = "Neeraj"` (line 21)
  - `PARTIES_TO_IGNORE = ["Pink Palace Babes", "Nyusha", "John Jonah"]` (line 22)
- [ ] Categories duplicated between Python and TypeScript with "Keep this in sync" comment
  - `server/constants.py` lines 60-77
  - `client/src/constants/categories.ts` lines 2-19

### Tasks

- [ ] Move `GATED_USERS` to environment variable or database configuration
- [ ] Move `USER_FIRST_NAME` to user profile from database
- [ ] Move `PARTIES_TO_IGNORE` to environment variable or user preferences
- [ ] Create shared category schema/validation
- [ ] Add build-time validation to ensure frontend/backend categories match
- [ ] Consider creating a `categories.json` that both backends import
- [ ] Update `.env.example` with new required variables

### Files to Modify

- `server/constants.py`
- `client/src/constants/categories.ts`
- `.env.example`
- Potentially add: `shared/categories.json`

---

## 2. Error Handling Consistency

**Priority:** HIGH (User Experience & Robustness)
**Impact:** Better debugging, consistent client error handling

### Issues

- [ ] Many blueprints have `# TODO: Exceptions` at top (6 files)
- [ ] Inconsistent error handling patterns across endpoints
- [ ] Some endpoints have try-catch, others don't
- [ ] Different error response formats across endpoints

### Tasks

#### Create Centralized Error Handling

- [ ] Create custom exception classes in `server/exceptions.py`:
  - `EventNotFoundException`
  - `LineItemNotFoundException`
  - `InvalidCategoryException`
  - `DuplicateEventException`
  - `ValidationException`
- [ ] Create error handler decorator for consistent responses
- [ ] Standardize error response format: `{"error": "message", "code": "ERROR_CODE", "details": {}}`

#### Update All Endpoints

- [ ] `server/resources/auth.py` - Remove TODO, add error handling
- [ ] `server/resources/event.py` - Remove TODO, add error handling
- [ ] `server/resources/line_item.py` - Remove TODO, add error handling
- [ ] `server/resources/monthly_breakdown.py` - Remove TODO, add error handling
- [ ] `server/resources/cash.py` - Remove TODO, add error handling
- [ ] `server/resources/splitwise.py` - Remove TODO, add error handling
- [ ] `server/resources/venmo.py` - Remove TODO, add error handling
- [ ] `server/resources/stripe.py` - Add consistent error handling

#### Frontend Error Handling

- [ ] Create error type definitions matching backend error codes
- [ ] Update `axiosInstance.tsx` interceptor to handle structured errors
- [ ] Create user-friendly error messages mapping
- [ ] Update all API hooks to properly type errors

### Files to Create

- `server/exceptions.py`
- `server/decorators/error_handler.py`
- `client/src/types/errors.ts`

### Files to Modify

- All files in `server/resources/`
- `client/src/utils/axiosInstance.tsx`
- `client/src/hooks/useApi.ts`

---

## 3. Type Safety

**Priority:** HIGH (Bug Prevention)
**Impact:** Catch bugs at development time, better IDE support

### Backend Type Safety

- [ ] Add complete type hints to all functions in `server/dao.py`
- [ ] Add complete type hints to all functions in `server/helpers.py`
- [ ] Add complete type hints to all utility functions in `server/utils/`
- [ ] Standardize on `Optional[X]` instead of `Union[X, None]`
- [ ] Add type hints to all resource blueprint functions
- [ ] Consider adding runtime validation with Pydantic for request bodies

### Frontend Type Safety

- [ ] Fix `client/src/data/EventHints.tsx` - Remove all `any` types (line 4 TODO)
- [ ] Enable stricter TypeScript settings in `tsconfig.json`:
  - Set `strict: true`
  - Set `noImplicitAny: true`
  - Set `strictNullChecks: true`
- [ ] Add Zod schemas for all API response validation
- [ ] Create proper interfaces for all component props
- [ ] Remove all `any` types throughout frontend
- [ ] Add runtime validation for API responses

### Files to Modify

- `server/dao.py`
- `server/helpers.py`
- `server/utils/*.py`
- `server/resources/*.py`
- `client/src/data/EventHints.tsx`
- `client/tsconfig.json`
- `client/src/hooks/useApi.ts` (add Zod validation)

### Files to Create

- `server/schemas/` directory with Pydantic models
- `client/src/schemas/` directory with Zod schemas

---

## 4. Code Duplication

**Priority:** MEDIUM (Maintenance & Consistency)
**Impact:** Reduces bugs from inconsistent implementations

### Backend Duplication

#### Serialization Functions

- [ ] Extract serialization logic from `dao.py`:
  - `_pg_serialize_line_item` (line 273)
  - `_pg_serialize_event` (line 304)
  - `_pg_serialize_user` (line 292)
- [ ] Create base serializer class or use Pydantic
- [ ] Create `server/serializers/` directory
- [ ] Implement serializers for each model type

#### Database Session Patterns

- [ ] Extract repeated `SessionLocal()` try-finally pattern (appears ~10 times in `dao.py`)
- [ ] Create context manager for database sessions
- [ ] Replace all manual session management with context manager

#### Query Patterns

- [ ] Extract common PostgreSQL query patterns
- [ ] Create repository classes for each model
- [ ] Move database logic from `dao.py` to repositories

### Frontend Duplication

#### Filter Logic

- [ ] Extract filter matching logic (repeated in `EventsPage.tsx`, `LineItemsPage.tsx`)
- [ ] Create `useFilteredData` custom hook
- [ ] Create generic filter components

#### Calculation Functions

- [ ] Extract calculation logic (`calculateSpending`, `calculateCashFlow`)
- [ ] Create `utils/calculations.ts`
- [ ] Consolidate into reusable functions

### Files to Create

- `server/serializers/line_item.py`
- `server/serializers/event.py`
- `server/serializers/user.py`
- `server/repositories/` directory
- `server/utils/db_context.py`
- `client/src/hooks/useFilteredData.ts`
- `client/src/utils/calculations.ts`

### Files to Modify

- `server/dao.py`
- `client/src/pages/EventsPage.tsx`
- `client/src/pages/LineItemsPage.tsx`

---

## 5. Database Session Management

**Priority:** MEDIUM (Resource Management)
**Impact:** Prevents resource leaks, reduces boilerplate

### Issues

- [ ] Repetitive try-finally pattern for database sessions in `dao.py`
- [ ] No centralized session lifecycle management
- [ ] Risk of forgetting to close sessions

### Tasks

- [ ] Create database session context manager:
  ```python
  @contextmanager
  def get_db_session():
      session = SessionLocal()
      try:
          yield session
          session.commit()
      except Exception:
          session.rollback()
          raise
      finally:
          session.close()
  ```
- [ ] Replace all manual session management in `dao.py`:
  - `_pg_get_all_line_items` (line 324)
  - `_pg_get_line_item_by_id` (line 360)
  - `_pg_get_user_by_id` (line 380)
  - `_pg_get_all_events` (line 396)
  - `_pg_get_event_by_id` (line 429)
  - `_pg_get_line_items_for_event` (line 453)
  - `_pg_get_categorized_data` (line 478)
  - `_pg_get_transactions` (line 514)
  - `_pg_get_all_bank_accounts` (line 543)
  - `_pg_get_user_by_email` (line 577)
- [ ] Update all utility functions using sessions
- [ ] Add session management to `dual_write.py` if needed

### Files to Create

- `server/utils/db_context.py`

### Files to Modify

- `server/dao.py`
- `server/utils/dual_write.py`
- All files in `server/utils/pg_*.py`

---

## 6. TODO Comment Cleanup

**Priority:** MEDIUM (Quick Wins)
**Impact:** Cleaner codebase, better task tracking

### Existing TODOs

#### Exceptions (Priority: Complete with Error Handling task)

- [ ] `server/resources/auth.py:25` - Remove after adding error handling
- [ ] `server/resources/event.py:26` - Remove after adding error handling
- [ ] `server/resources/line_item.py:15` - Remove after adding error handling
- [ ] `server/resources/monthly_breakdown.py:16` - Remove after adding error handling
- [ ] `server/resources/cash.py:24` - Remove after adding error handling
- [ ] `server/resources/splitwise.py:25` - Remove after adding error handling
- [ ] `server/resources/venmo.py:26` - Remove after adding error handling

#### Feature TODOs

- [ ] `server/application.py:248` - "Need to add webhooks for updates"
  - Create GitHub issue for webhook implementation
  - Remove comment or add issue reference
- [ ] `server/resources/stripe.py:296` - "This gets all transactions ever. We should only get those that we don't have"
  - Implement incremental transaction fetching
  - Or create GitHub issue and reference it
- [ ] `client/src/data/EventHints.tsx:4` - "Remove 'any' types"
  - Complete with Type Safety task

#### Configuration TODOs (Complete with Configuration task)

- [ ] `server/resources/splitwise.py:26` - "Can I remove MOVING_DATE_POSIX"
  - Analyze usage and remove if unused
- [ ] `server/resources/splitwise.py:27` - "Can I remove PARTIES_TO_IGNORE"
  - Move to environment variable or remove
- [ ] `server/resources/venmo.py:27` - "Can I remove MOVING_DATE_POSIX"
  - Analyze usage and remove if unused
- [ ] `server/resources/venmo.py:28` - "Can I remove PARTIES_TO_IGNORE"
  - Move to environment variable or remove

#### Integration TODOs

- [ ] `server/resources/splitwise.py:29` - "Integrate with Splitwise OAuth"
  - Create GitHub issue for OAuth implementation
  - Add to roadmap
- [ ] `server/resources/splitwise.py:49` - "What if an expense is deleted? What if it's part of an event?"
  - Document expected behavior
  - Create GitHub issue if needs implementation
- [ ] `server/resources/splitwise.py:89` - "Set up comma separated list of responsible parties"
  - Create GitHub issue or implement

#### Performance TODOs

- [ ] `server/resources/venmo.py:62` - "This might have one extra network call when we break out of the loop"
  - Analyze and optimize or document why acceptable

### Tasks

- [ ] Create GitHub issues for all feature TODOs
- [ ] Replace TODO comments with issue references
- [ ] Remove completed TODOs
- [ ] Document decisions for "Can I remove X" TODOs

---

## 7. Documentation

**Priority:** MEDIUM (Long-term Maintenance)
**Impact:** Easier onboarding, better collaboration

### Issues

- [ ] Inconsistent docstring coverage across codebase
- [ ] Mix of documentation styles
- [ ] No API documentation (Swagger/OpenAPI)
- [ ] Missing setup/deployment documentation

### Tasks

#### Backend Documentation

- [ ] Add Google-style docstrings to all public functions in:
  - `server/application.py`
  - `server/dao.py`
  - `server/helpers.py`
  - All files in `server/resources/`
  - All files in `server/utils/`
- [ ] Document all API endpoints with:
  - Request format
  - Response format
  - Error codes
  - Example usage
- [ ] Create API documentation (consider FastAPI migration or add flask-swagger)

#### Frontend Documentation

- [ ] Add JSDoc comments to all exported functions
- [ ] Document all custom hooks with usage examples
- [ ] Add prop type documentation to complex components
- [ ] Document context providers

#### General Documentation

- [ ] Update README.md with comprehensive setup instructions
- [ ] Add CONTRIBUTING.md with development guidelines
- [ ] Add ARCHITECTURE.md explaining system design
- [ ] Document migration strategy from MongoDB to PostgreSQL
- [ ] Add deployment documentation

### Files to Create

- `CONTRIBUTING.md`
- `ARCHITECTURE.md`
- `docs/API.md`
- `docs/DEPLOYMENT.md`
- `docs/MIGRATION.md`

### Files to Modify

- `README.md`
- All Python files (add docstrings)
- All TypeScript files (add JSDoc)

---

## 8. Logging Improvements

**Priority:** LOW (Debugging & Operations)
**Impact:** Better debugging, easier log analysis

### Issues

- [ ] Inconsistent log formatting (f-strings vs concatenation)
- [ ] Mix of log levels (could be better aligned)
- [ ] No request tracing capability
- [ ] No structured logging for parsing

### Tasks

#### Standardize Logging Format

- [ ] Convert all string concatenation logs to f-strings:
  - `server/application.py:157` - "Initiating scheduled refresh at " + str(datetime.now())
- [ ] Review and align log levels throughout codebase
- [ ] Create logging guidelines document

#### Add Structured Logging

- [ ] Implement structured logging (JSON format for production)
- [ ] Add request ID to all logs for tracing
- [ ] Add user ID to authenticated request logs
- [ ] Add timing information to expensive operations

#### Add Request Tracing

- [ ] Create middleware to add request IDs
- [ ] Pass request IDs through all function calls
- [ ] Log request start/end with IDs

### Files to Modify

- `server/application.py`
- All files in `server/resources/`
- `server/dao.py`
- All files in `server/utils/`

### Files to Create

- `server/middleware/request_id.py`
- `docs/LOGGING.md`

---

## 9. Magic Strings & Numbers

**Priority:** LOW (Code Quality)
**Impact:** Prevents typos, easier refactoring

### Issues

- [ ] API paths as strings throughout hooks
- [ ] Status values as strings ("active", "inactive")
- [ ] Payment methods as strings
- [ ] Category names as strings
- [ ] Event sources as strings ("stripe", "venmo", "splitwise", "cash")

### Tasks

#### Backend Constants

- [ ] Create `server/constants/api_routes.py` with all route paths
- [ ] Create enum for account statuses (`AccountStatus.ACTIVE`, `AccountStatus.INACTIVE`)
- [ ] Create enum for transaction sources (`Source.STRIPE`, `Source.VENMO`, etc.)
- [ ] Replace all string literals with constants

#### Frontend Constants

- [ ] Create `client/src/constants/api-routes.ts` with all API endpoints
- [ ] Create TypeScript enums for statuses
- [ ] Create constants for payment methods
- [ ] Update all API calls to use route constants

### Files to Create

- `server/constants/api_routes.py`
- `server/constants/enums.py`
- `client/src/constants/api-routes.ts`
- `client/src/constants/enums.ts`

### Files to Modify

- `client/src/hooks/useApi.ts`
- All files using string literals for API paths
- All files using status strings

---

## 10. Component Organization

**Priority:** LOW (Frontend Architecture)
**Impact:** Better reusability, easier testing

### Issues

- [ ] Large component files (`App.tsx`, `EventsPage.tsx`)
- [ ] Navigation code duplicated between desktop and mobile
- [ ] Repeated JSX patterns for filters
- [ ] Some components handle multiple responsibilities

### Tasks

#### Extract Components

- [ ] Extract navigation from `App.tsx` into `components/Navigation.tsx`
- [ ] Extract mobile navigation into `components/MobileNavigation.tsx`
- [ ] Create generic `FilterBar` component that takes configuration
- [ ] Split `EventsPage.tsx` into smaller components:
  - `EventsPageHeader`
  - `EventsFilters`
  - `EventsSummary`
  - `EventsList`
  - `EventsTable`
- [ ] Split `LineItemsPage.tsx` similarly

#### Create Reusable Components

- [ ] Create `SummaryCard` component (used in multiple pages)
- [ ] Create `FilterSection` component for collapsible filters
- [ ] Create `DateRangeFilter` component (used in multiple places)

#### Apply Single Responsibility Principle

- [ ] Review all page components for single responsibility
- [ ] Extract business logic into custom hooks
- [ ] Separate data fetching from presentation

### Files to Create

- `client/src/components/Navigation.tsx`
- `client/src/components/MobileNavigation.tsx`
- `client/src/components/FilterBar.tsx`
- `client/src/components/SummaryCard.tsx`
- `client/src/components/FilterSection.tsx`
- `client/src/components/DateRangeFilter.tsx`
- `client/src/pages/EventsPage/` directory with sub-components

### Files to Modify

- `client/src/App.tsx`
- `client/src/pages/EventsPage.tsx`
- `client/src/pages/LineItemsPage.tsx`

---

## Implementation Strategy

### Phase 1: High-Priority Security & Stability

1. Configuration & Constants
2. Error Handling Consistency
3. Type Safety

**Estimated Effort:** 2-3 weeks

### Phase 2: Code Quality & Maintenance

4. Code Duplication
5. Database Session Management
6. TODO Comment Cleanup

**Estimated Effort:** 1-2 weeks

### Phase 3: Long-term Improvements

7. Documentation
8. Logging Improvements
9. Magic Strings & Numbers
10. Component Organization

**Estimated Effort:** 2-3 weeks

---

## Tracking Progress

- [ ] Phase 1 Complete
- [ ] Phase 2 Complete
- [ ] Phase 3 Complete

**Total Estimated Effort:** 5-8 weeks (depending on team size and availability)

---

## Notes

- All improvements maintain existing functionality
- No breaking changes to API contracts
- All changes should include tests
- Consider creating feature branches for each major task
- Review and update this document as improvements are completed
