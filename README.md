# Budget.RIP

A personal budgeting app that aggregates transactions from Stripe, Venmo, and Splitwise.

## Quick Start

### Server

```bash
cd server
make dev-setup          # Install dependencies with uv
uv run alembic upgrade head  # Apply database migrations
uv run python application.py # Start server on port 4242
```

### Client

```bash
cd client
npm install
npm start               # Start client on port 3000
```

## Operating Budget.RIP

### Database

The app uses **PostgreSQL** with **Alembic** for migrations.

**Apply migrations:**
```bash
cd server
uv run alembic upgrade head
```

**Create a new migration** (after changing models in `models/sql_models.py`):
```bash
uv run alembic revision --autogenerate -m "Add column_name to table"
```

**Other useful commands:**
```bash
uv run alembic current      # Show current migration version
uv run alembic history      # Show migration history
uv run alembic downgrade -1 # Undo last migration
```

### Testing

```bash
cd server
make test           # Run all tests (runs twice: MongoDB mode, then PostgreSQL mode)
make test-quick     # Run tests without verbose output
make lint           # Check code style
make lint-fix       # Auto-fix code style issues
```

### Environment Variables

Create a `.env` file in `server/` with:

```bash
# Database (required)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USERNAME=your_username
DATABASE_PASSWORD=your_password
DATABASE_NAME=budget_db
DATABASE_SSL_MODE=prefer        # Use "require" for production

# Integrations
STRIPE_LIVE_API_SECRET_KEY=sk_live_...
STRIPE_CUSTOMER_ID=cus_...
VENMO_ACCESS_TOKEN=...
SPLITWISE_API_KEY=...
SPLITWISE_CONSUMER_KEY=...
SPLITWISE_CONSUMER_SECRET=...

# Auth
JWT_SECRET_KEY=your-secret-key
JWT_COOKIE_DOMAIN=localhost

# Optional
MONGO_URI=mongodb://localhost:27017/flask_db  # Legacy, being phased out
READ_FROM_POSTGRESQL=false                     # Set true to read from PostgreSQL
CORS_ALLOWED_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
```

### Connecting to Production Database

```bash
# Set production credentials
export DATABASE_HOST="your-prod-host.com"
export DATABASE_PASSWORD="your-prod-password"
# ... other vars

# Apply migrations
cd server
uv run alembic upgrade head

# Or connect directly with psql
psql "postgresql://$DATABASE_USERNAME:$DATABASE_PASSWORD@$DATABASE_HOST:$DATABASE_PORT/$DATABASE_NAME?sslmode=require"
```

## Development Philosophy

- **Every line of code is a liability** - write only what's necessary
- **Prefer editing over adding** - extend existing functions rather than creating new ones
- **Favor maintainability** - simple, clear solutions over clever ones
- **Prudent comments** - explain *why*, not *what*
