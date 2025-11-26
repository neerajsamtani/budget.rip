# Onboarding Guide for Budget.RIP

Welcome to Budget.RIP! This guide is designed for new engineers joining the project. If you have an understanding of Computer Science fundamentals but aren't familiar with the specific technologies used in this codebase, this guide will help you get up to speed.

## Project Overview

Budget.RIP (Budgit) is a full-stack personal finance tracking application built as a monorepo with:
- **Frontend**: React + TypeScript + Vite
- **Backend**: Python + Flask + PostgreSQL
- **External Integrations**: Stripe, Venmo, Splitwise

The application aggregates financial transactions from multiple sources and provides budgeting, categorization, and visualization features.

---

## 🎯 Priority 1: Core Languages & Frameworks

### TypeScript (Frontend)
- JavaScript fundamentals, then TypeScript's type system
- Learn: types, interfaces, generics, type inference
- **Resource**: [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)

### Python 3.12+ (Backend)
- Type hints, dataclasses, context managers
- Python packaging with `pyproject.toml`
- **Resource**: [Real Python](https://realpython.com/)

---

## 🎯 Priority 2: Web Frameworks

### React 18 (Frontend)
- Functional components and hooks (`useState`, `useEffect`, `useContext`)
- Custom hooks pattern (used heavily in `client/src/hooks/`)
- React Router for client-side routing
- **Resource**: [React docs](https://react.dev/)

### Flask (Backend)
- Route decorators, blueprints, request/response handling
- Application factory pattern
- **Resource**: [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)

---

## 🎯 Priority 3: Data Layer

### PostgreSQL & SQLAlchemy
- SQL fundamentals (JOINs, indexes, constraints)
- SQLAlchemy ORM: models, relationships, queries
- **Alembic** for database migrations (see `server/alembic/`)
- **Resource**: [SQLAlchemy Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)

### TanStack Query (React Query)
- Server state management vs. client state
- Queries, mutations, caching, invalidation
- This codebase uses it extensively in `client/src/hooks/`
- **Resource**: [TanStack Query docs](https://tanstack.com/query/latest)

---

## 🎯 Priority 4: Styling & UI

### Tailwind CSS
- Utility-first CSS approach
- Responsive design with breakpoints
- **Resource**: [Tailwind docs](https://tailwindcss.com/docs)

### Radix UI
- Accessible, unstyled component primitives
- Used for dialogs, selects, tooltips in this codebase
- **Resource**: [Radix UI docs](https://www.radix-ui.com/)

---

## 🎯 Priority 5: Authentication & Security

### JWT (JSON Web Tokens)
- How token-based auth works
- HTTP-only cookies for security
- Flask-JWT-Extended library (see `server/resources/auth.py`)
- **Resource**: [jwt.io](https://jwt.io/introduction)

---

## 🎯 Priority 6: External APIs

### Stripe API
- Financial Connections for bank account linking
- Webhooks and API versioning
- This is a core integration in the app (see `server/resources/stripe.py`)
- **Resource**: [Stripe docs](https://stripe.com/docs)

### REST API Design
- HTTP methods, status codes, request/response patterns
- How the backend exposes endpoints in `server/resources/`

---

## 🎯 Priority 7: Development Tools

### Git & GitHub
- Branching, merging, pull requests
- GitHub Actions for CI/CD (see `.github/workflows/`)

### Vite (Frontend Build)
- Modern bundler replacing Webpack
- Hot Module Replacement (HMR)
- Configuration in `client/vite.config.ts`
- **Resource**: [Vite docs](https://vitejs.dev/)

### Testing
- **Frontend**: Jest + React Testing Library + MSW (API mocking)
- **Backend**: pytest + pytest-mock
- Writing unit and integration tests

---

## 🎯 Priority 8: Environment & DevOps

### Environment Variables
- Using `.env` files, `python-dotenv`
- Never committing secrets
- See required env vars in `server/application.py`

### Docker Basics (Helpful Context)
- Understanding containerized services (PostgreSQL, MongoDB in CI)

### Make (Task Automation)
- Read the `Makefile` in `server/` to understand common commands:
  - `make test` - Run tests
  - `make lint` - Lint code
  - `make migrate` - Run database migrations

---

## 📚 Suggested Learning Order

| Week | Focus Area |
|------|------------|
| 1-2 | TypeScript fundamentals, React basics |
| 3-4 | Python type hints, Flask basics |
| 5-6 | SQL, SQLAlchemy, database migrations |
| 7-8 | React Query, Tailwind CSS |
| 9-10 | JWT auth, Stripe API basics |
| 11-12 | Testing (Jest, pytest), Git workflows |

---

## 💡 Codebase-Specific Tips

### 1. Understand the Data Model
Start by reading `server/models/sql_models.py` to understand the core entities:
- Users
- Bank Accounts
- Categories
- Payment Methods
- Tags
- Transactions & Line Items
- Events

### 2. Trace a Feature End-to-End
Pick a simple feature like viewing events and follow it through:
1. **Frontend**: `client/src/pages/EventsPage.tsx`
2. **API Hook**: `client/src/hooks/useEvents.ts` (or similar)
3. **Backend Route**: `server/resources/event.py`
4. **Database Model**: `server/models/sql_models.py`

### 3. Run the Tests
```bash
# Backend
cd server
make test

# Frontend
cd client
npm test
```

Study test files to understand how components and APIs are tested.

### 4. Study the Hooks
Custom React hooks in `client/src/hooks/` encapsulate most data fetching logic. Understanding these will help you see how the frontend interacts with the backend.

### 5. Understand the Migration Architecture
The codebase is transitioning from MongoDB to PostgreSQL. See `server/MONGODB_TO_POSTGRES_MIGRATION.md` for details. This dual-database pattern is temporary but important to understand.

---

## Key Technologies at a Glance

### Frontend Stack
- **React 18.3.1** - UI framework
- **TypeScript 4.9.5** - Type safety
- **Vite 7.1.7** - Build tool
- **TanStack Query 5.90.7** - Server state management
- **Tailwind CSS 4.1.13** - Styling
- **Radix UI** - Accessible components
- **React Router 6.4.4** - Routing
- **Plotly.js** - Data visualization
- **Axios** - HTTP client

### Backend Stack
- **Flask 3.1.2** - Web framework
- **SQLAlchemy 2.0.44** - ORM
- **Alembic 1.17.2** - Migrations
- **PostgreSQL 16** - Database
- **Flask-JWT-Extended** - Authentication
- **Gunicorn 23.0.0** - WSGI server
- **pytest** - Testing

### External Services
- **Stripe** - Bank account linking and transactions
- **Venmo API** - Payment syncing
- **Splitwise API** - Expense sharing

---

## Development Workflow

### Initial Setup
1. Clone the repository
2. Set up environment variables (see `.env.example` if available)
3. Install dependencies:
   ```bash
   # Backend
   cd server
   uv sync

   # Frontend
   cd client
   npm install
   ```
4. Run migrations:
   ```bash
   cd server
   make migrate
   ```

### Running Locally
```bash
# Backend
cd server
flask run

# Frontend (separate terminal)
cd client
npm run dev
```

### Before Committing
```bash
# Backend
cd server
make lint
make test

# Frontend
cd client
npm run lint
npm test
```

---

## Getting Help

- **Documentation**: Check the `README.md` in root and `server/` directories
- **Migration Guide**: See `server/MONGODB_TO_POSTGRES_MIGRATION.md`
- **Testing Guide**: See `server/TESTING.md`
- **Code Review**: Don't hesitate to ask questions in PRs

---

## Next Steps

Once you're comfortable with the basics:
1. Check out [QUICK_WINS.md](./QUICK_WINS.md) for beginner-friendly contribution ideas
2. Pick a small issue or TODO from the codebase
3. Submit your first PR!

Welcome to the team! 🎉
