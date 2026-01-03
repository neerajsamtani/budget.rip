# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Philosophy

**"Every line of code is a liability"**

- **Prefer editing over adding**: Modify existing functions to be more extensible rather than creating new ones
- **Minimize code**: Write only what's necessary to accomplish the task - no more, no less
- **Prioritize readability**: Code should be easily understood by developers jumping into the codebase. 
- **Prudent comments**: Only add comments for things that are not obvious when reading the code, or when summarizing large chunks of code when a comment would greatly improve readability. Comments should generally talk about _why_ the code is doing what it's doing and not just _what_ the code is doing.
- **Favor maintainability**: Simple, clear solutions over clever ones
- **Keep it accessible**: New developers should be able to quickly understand and make changes

## Project Overview

Budgit is a personal finance tracking application with a client-server architecture. The app aggregates financial transactions from multiple sources (Venmo, Splitwise, Stripe, manual cash entries) and provides categorization, review workflows, and analytics.

## Architecture

### Monorepo Structure
- `client/` - React frontend (Vite + TypeScript)
- `server/` - Flask backend (Python)

### Key Concepts
- **Line Items**: Core data model representing individual financial transactions from any source
- **Events**: Higher-level groupings of line items (e.g., trips, shared expenses)
- **Data Flow**: External APIs → Raw data collections → Normalized line items → User review → Categorized events
- **Review Workflow**: Line items start uncategorized and are reviewed/assigned to events through the UI

## Tech Stack

### Client (Vite + React)
- React 18.3 with TypeScript 4.9
- Vite 7 build tool
- shadcn/ui components
- Tailwind CSS 4 for styling
- React Router 6 for routing
- Context API for state management (`LineItemsContext`)
- Axios for API calls via `axiosInstance`, leveraging TanStack Query
- Sonner for toast notifications
- Jest + React Testing Library for tests
- Dev server runs on `dev.localhost`

### Server (Flask + PostgreSQL)
- Flask 3.0 with Python 3.13
- SQLAlchemy 2.0 with PostgreSQL
- Alembic for PostgreSQL schema migrations
- Flask-JWT-Extended for auth (JWT in cookies)
- Flask-Bcrypt for password hashing
- Blueprint-based route organization (`resources/` directory)
- External integrations: Stripe API, Venmo API, Splitwise API
- pytest for testing (uses SQLite in-memory)

### Database

PostgreSQL

Tables defined in `models/sql_models.py`:
- `transactions` - raw transaction data from external APIs
- `line_items` - normalized line items with foreign keys
- `events` - event groupings
- `categories` - expense categories
- `payment_methods` - payment method lookup
- `event_line_items` - junction table for many-to-many
- `tags`, `event_tags` - tagging system
- `users` - user accounts
- `bank_accounts` - bank account metadata

## Common Commands

### Client Development
```bash
cd client
npm start                 # Start dev server on dev.localhost
npm run build            # Production build
npm run test             # Run all tests once
npm run test:watch       # Run tests in watch mode
npm run analyze          # Build and visualize bundle size
```

### Server Development
```bash
cd server
uv run python -m pytest                    # Run all tests
uv run python -m pytest tests/test_auth.py # Run specific test file
uv run python -m pytest -v                 # Verbose test output
uv run python application.py               # Run Flask server locally

# Prefer the Makefile for common tasks:
make help                           # Show all available commands
make test                           # Run all tests with verbose output
make test-quick                     # Run tests without verbose output
make test-coverage                  # Run tests with coverage report
make lint                           # Check code with ruff (linting + formatting)
make lint-fix                       # Auto-fix code issues with ruff
make install                        # Install/update dependencies
make pg-dump                        # Create PostgreSQL database dump (requires PGPASSWORD env var)
```

**Dependencies are managed by uv**. Use `uv sync` to install/update dependencies, and `uv run <command>` to run commands in the managed environment.

### Database Migrations (Alembic)
```bash
cd server
uv run alembic revision --autogenerate -m "description" # Generate migration
uv run alembic upgrade head                             # Apply all pending migrations
uv run alembic downgrade -1                             # Rollback one migration
uv run alembic current                                  # Show current revision
uv run alembic history                                  # Show migration history
```

### Running Single Tests
- **Client**: `npm test -- App.test.tsx` or `npm run test:watch` then press `p` to filter by filename
- **Server**: `uv run python -m pytest tests/test_auth.py::test_function_name`

## Code Conventions

### Client (TypeScript/React)
- Use functional components with hooks
- Use ES modules (`import`/`export`)
- Use `@/` prefix for absolute imports (maps to `src/`)
- Components in `src/components/`, pages in `src/pages/`
- shadcn/ui components in `src/components/ui/`
- Utility functions in `src/utils/`
- Use TanStack Query for all API calls, which are registered in `src/hooks/useApi.ts`
- Toast notifications via `showSuccessToast()` and `showErrorToast()` from `src/utils/toast-helpers.ts`
- State management via Context API with `useReducer` pattern in `src/contexts/`
  - Line items use reducer with actions: `populate_line_items`, `toggle_line_item_select`, `remove_line_items`
  - Separate contexts for state (`useLineItems()`) and dispatch (`useLineItemsDispatch()`)

### Server (Python/Flask)
- Routes organized as Flask Blueprints in `resources/` directory
- Database operations:
  - PostgreSQL models in `models/sql_models.py`
  - PostgreSQL bulk operations in `utils/pg_bulk_ops.py`
  - PostgreSQL event operations in `utils/pg_event_operations.py`
  - Data access layer in `dao.py` (abstraction over SQL models)
- Helper functions in `helpers.py`
- API clients in `clients.py`
- Constants in `constants.py` (includes categories, date filters, API keys)
- Type hints encouraged
- Legacy collection names defined as string constants in `dao.py` for backwards compatibility

### API Patterns
- All API routes prefixed with `/api/`
- Authentication via JWT cookies (configured for cross-origin)
  - Login sets JWT in HTTP-only cookie
  - `axiosInstance` configured with `withCredentials: true` to send cookies
  - Protected endpoints use `@jwt_required()` decorator from Flask-JWT-Extended
- Response format: `{"data": ..., "message": ...}`
- Error handling: Use `showErrorToast()` on client, server returns appropriate status codes

### Categories
Categories are defined in `server/constants.py` and must be kept in sync with the frontend:
- All, Alcohol, Dining, Entertainment, Forma, Groceries, Hobbies, Income, Investment, Medical, Rent, Shopping, Subscription, Transfer, Transit, Travel
- There is in-progress work to leverage the Categories table in Postgres to power this, instead of having defined constants.

### Data Normalization Pattern
External API data follows this flow:
1. **Raw data ingestion**: API responses stored in `transactions` table with source tracking
2. **Transformation**: Functions (`venmo_to_line_items`, `splitwise_to_line_items`, etc.) normalize raw transaction data
3. **Line item creation**: Normalized data stored in `line_items` table with foreign keys to:
   - `transaction_id` - links to source transaction
   - `payment_method_id` - links to payment method lookup table
4. **Deduplication**: Line items are deduplicated based on `transaction_id` to prevent duplicates from API re-fetches
5. **User review**: Line items reviewed and assigned to events via UI
6. **Event groupings**: Many-to-many relationship via `event_line_items` junction table

## Key Files

### Client
- `src/App.tsx` - Main app component with routing and navbar
- `src/contexts/LineItemsContext.tsx` - Global state for line items with reducer pattern
- `src/hooks/useApi.ts` - All API calls configured via TanStack Query
- `src/utils/axiosInstance.ts` - Configured Axios instance
- `src/utils/toast-helpers.ts` - Toast notification utilities
- `vite.config.ts` - Vite configuration with path aliases and chunk splitting

### Server
- `application.py` - Flask app setup, blueprint registration, JWT config
- `dao.py` - Data access layer (abstraction over PostgreSQL models)
- `models/sql_models.py` - SQLAlchemy models for PostgreSQL
- `utils/pg_bulk_ops.py` - PostgreSQL bulk upsert operations for transactions and line items
- `utils/pg_event_operations.py` - Event-specific database operations
- `constants.py` - Environment variables, categories, date filters
- `resources/*.py` - Blueprint modules for different API endpoints:
  - `auth.py` - Authentication endpoints
  - `line_item.py` - Line item CRUD
  - `event.py` - Event management
  - `venmo.py`, `splitwise.py`, `stripe.py`, `cash.py` - External data source integrations
  - `monthly_breakdown.py` - Analytics endpoints
- `alembic/` - Database migration files
- `migrations/` - Legacy migration scripts (MongoDB → PostgreSQL migration completed)

## Environment Variables

### Client (.env)
- `VITE_STRIPE_PUBLIC_KEY` - Stripe publishable key
- API calls default to relative URLs (proxied in dev)

### Server (.env)
- PostgreSQL connection (individual components to avoid URL encoding issues):
  - `DATABASE_HOST` - PostgreSQL host (required for production, defaults to `localhost`)
  - `DATABASE_PORT` - PostgreSQL port (defaults to `5432`)
  - `DATABASE_USERNAME` - Database user (required for production)
  - `DATABASE_PASSWORD` - Database password (required for production)
  - `DATABASE_NAME` - Database name (required for production)
  - `DATABASE_SSL_MODE` - SSL mode (defaults to `prefer`)
  - Tests: `DATABASE_HOST=sqlite` triggers SQLite in-memory mode
- `STRIPE_LIVE_API_SECRET_KEY` - Stripe secret key
- `STRIPE_CUSTOMER_ID` - Stripe customer ID
- `VENMO_ACCESS_TOKEN` - Venmo API token
- `SPLITWISE_CONSUMER_KEY`, `SPLITWISE_CONSUMER_SECRET`, `SPLITWISE_API_KEY` - Splitwise OAuth
- `JWT_SECRET_KEY` - JWT signing key (defaults to `testSecretKey123` for development)
- `JWT_COOKIE_DOMAIN` - Cookie domain for JWT (for cross-origin authentication)
- `CORS_ALLOWED_ORIGINS` - Comma-separated list of allowed origins (defaults to `http://dev.localhost:5173`)
- `LOG_LEVEL` - Logging level (defaults to `INFO`)

## Testing Notes

### Test Naming Convention
Test names should read as statements of fact about system behavior, not as descriptions of what the test does:
- **Use passive voice**: `'modal is rendered when show is true'` not `'renders modal when show is true'`
- **State the outcome**: `'API error is handled gracefully'` not `'handles API error gracefully'`
- **Be specific**: `'line items are fetched on mount'` not `'fetches data'`

Common transformations:
- `'renders X'` → `'X is rendered'`
- `'calls X when Y'` → `'X is called when Y'`
- `'handles X'` → `'X is handled'`
- `'shows X'` → `'X is shown'`
- `'returns X'` → `'X is returned'`

### Client
- Tests use Jest with jsdom environment
- Setup file at `src/setupTests.ts`
- MSW for API mocking
- Coverage reports in `coverage/` directory

### Server
- pytest with fixtures in `tests/conftest.py`
- Test files in `server/tests/` directory
- **Test Database Isolation** (configured in `tests/conftest.py`):
  - Uses SQLite in-memory database for all tests
  - Environment variables `DATABASE_HOST=sqlite` and `DATABASE_NAME=:memory:` set before imports
  - Tables created/destroyed for each test to ensure isolation
  - **CRITICAL**: Tests never touch production databases
- All tests use the same SQLAlchemy models as production, ensuring consistency

## Development Workflow

### Local Development Setup
1. **Database**:
   - PostgreSQL required (set `DATABASE_HOST`, `DATABASE_USERNAME`, `DATABASE_PASSWORD`, `DATABASE_NAME`)
   - Run Alembic migrations: `cd server && uv run alembic upgrade head`
2. **Server**: Navigate to `server/`, run `uv sync` to install dependencies, then `uv run python application.py`
3. **Client**: Navigate to `client/`, run `nvm use 22` to switch to Node.js v22, then `npm start` (dev server runs on `dev.localhost`)

## Migration Context

Recent major migrations:
- ✅ Bootstrap → shadcn/ui + Tailwind CSS (completed)
- ✅ Create React App → Vite (completed)
- ✅ React 17 → React 18 (completed)
- ✅ **pip/virtualenv → uv** (completed):
  - Dependencies now managed via uv (Astral's fast Python package manager)
  - pyproject.toml contains [project] section with production and dev dependencies
  - uv.lock file ensures reproducible builds
  - GitHub Actions uses uv for CI/CD
  - Vercel configured to use uv for deployments
  - All commands now use `uv run <command>` or Makefile targets
- ✅ **MongoDB → PostgreSQL** (completed):
  - All data migrated to PostgreSQL
  - MongoDB dependencies removed
  - All CRUD operations now use SQLAlchemy models
  - Legacy migration documentation in `server/MONGODB_TO_POSTGRES_MIGRATION.md`
- 📋 Planning: Flask → FastAPI (see `server/FLASK_TO_FASTAPI_MIGRATION_PLAN.md`)
