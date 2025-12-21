.PHONY: help test test-phase3 test-watch test-coverage test-quick install lint lint-fix clean dev-setup pg-dump

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
