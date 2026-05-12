.PHONY: help test test-phase3 test-watch test-coverage test-quick install lint lint-fix clean dev-setup pg-dump openapi types api api-check

# Dummy env vars so application.py imports cleanly when generating the OpenAPI spec
# (mirrors the test env: SQLite in-memory, placeholder secrets)
OPENAPI_ENV := TESTING=true DATABASE_HOST=sqlite DATABASE_NAME=:memory: \
	JWT_SECRET_KEY=x JWT_COOKIE_DOMAIN=x \
	VENMO_ACCESS_TOKEN=x \
	SPLITWISE_CONSUMER_KEY=x SPLITWISE_CONSUMER_SECRET=x SPLITWISE_API_KEY=x \
	STRIPE_LIVE_API_SECRET_KEY=x STRIPE_CUSTOMER_ID=x

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install/update dependencies
	@echo "Installing dependencies with uv..."
	@uv sync
	@echo "✓ Dependencies installed"

test: ## Run all tests
	@echo "Running tests..."
	@uv run pytest tests/ -v

test-phase3: ## Run Phase 3 migration tests only
	@uv run pytest tests/test_phase3_migration.py -v

test-watch: ## Run tests in watch mode
	@uv run pytest tests/ -v --looponfail

test-coverage: ## Run tests with coverage report
	@uv run pytest tests/ -v --cov=. --cov-report=html --cov-report=term

test-quick: ## Run tests without verbose output
	@uv run pytest tests/

lint: ## Check code with ruff (linting + formatting)
	@echo "Checking code with ruff..."
	@uv run ruff check .
	@uv run ruff format --check .
	@echo "✓ All checks passed"

lint-fix: ## Fix code issues with ruff (auto-fix + format)
	@echo "Fixing code issues with ruff..."
	@uv run ruff check --fix .
	@uv run ruff format .
	@echo "✓ Code fixed and formatted"

clean: ## Remove virtual environment and cache files
	rm -rf .venv
	rm -rf .pytest_cache
	rm -rf __pycache__
	rm -rf .coverage
	rm -rf htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned up"

dev-setup: install ## Set up development environment
	@echo "✓ Development environment ready"
	@echo ""
	@echo "Dependencies are managed by uv:"
	@echo "  uv sync                    # Install/update dependencies"
	@echo "  uv run <command>           # Run commands in the uv environment"
	@echo "  uv add <package>           # Add a production dependency"
	@echo "  uv add --dev <package>     # Add a development dependency"
	@echo ""
	@echo "To run tests:"
	@echo "  make test                  # Run all tests"
	@echo "  make test-quick            # Run tests without verbose output"
	@echo ""
	@echo "To run the server:"
	@echo "  uv run python application.py"

openapi: ## Regenerate server/openapi.json from application.spec
	@echo "Regenerating openapi.json..."
	@$(OPENAPI_ENV) uv run python scripts/dump_openapi.py > openapi.json
	@echo "✓ openapi.json updated"

types: openapi ## Regenerate client TypeScript types from openapi.json
	@echo "Regenerating client TypeScript types..."
	@cd ../client && npm run generate:api:from-file
	@echo "✓ api.generated.ts updated"

api: types ## Regenerate both openapi.json and client TypeScript types (alias for types)

api-check: ## Fail if openapi.json or api.generated.ts is stale (for CI)
	@$(MAKE) --no-print-directory types
	@git diff --exit-code openapi.json ../client/src/types/api.generated.ts \
		|| (echo "✗ openapi.json or api.generated.ts is out of date. Run 'make api' and commit."; exit 1)
	@echo "✓ openapi.json and api.generated.ts are up to date"

pg-dump: ## Create PostgreSQL database dump (requires PGPASSWORD env var)
	@if [ -z "$$PGPASSWORD" ]; then \
		echo "Error: PGPASSWORD environment variable is not set"; \
		echo "Usage: PGPASSWORD=your_password make pg-dump"; \
		exit 1; \
	fi
	@echo "Creating PostgreSQL dump..."
	@pg_dump -h us-west-3.pg.psdb.cloud -p 5432 \
		-U pscale_api_jlyfrqc8m3a2.msciuxoprsk4 \
		-d postgres --clean --if-exists \
		> budgit_postgres_dump_$$(date +%Y_%m_%d).sql
	@echo "✓ Dump created: budgit_postgres_dump_$$(date +%Y_%m_%d).sql"
