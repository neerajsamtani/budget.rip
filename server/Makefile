.PHONY: help test test-phase3 test-watch venv clean install lint lint-fix

VENV := env
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv: ## Create virtual environment and install dependencies
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV); \
	fi
	@echo "Installing dependencies..."
	@$(PIP) install --upgrade pip setuptools wheel -q
	@$(PIP) install -r requirements.txt -q
	@touch $(VENV)/.deps_installed
	@echo "✓ Virtual environment ready"

install: venv ## Install/update dependencies (alias for venv)

test: venv ## Run all tests
	@echo "Running tests with READ_FROM_POSTGRESQL=false..."
	@READ_FROM_POSTGRESQL=false $(PYTHON) -m pytest tests/ -v
	@echo "Running tests with READ_FROM_POSTGRESQL=true..."
	@READ_FROM_POSTGRESQL=true $(PYTHON) -m pytest tests/ -v

test-phase3: venv ## Run Phase 3 migration tests only
	@$(PYTEST) tests/test_phase3_migration.py -v

test-watch: venv ## Run tests in watch mode
	@$(PYTEST) tests/ -v --looponfail

test-coverage: venv ## Run tests with coverage report
	@$(PYTEST) tests/ -v --cov=. --cov-report=html --cov-report=term

test-quick: venv ## Run tests without verbose output
	@$(PYTEST) tests/

lint: venv ## Check code with ruff (linting + formatting)
	@echo "Checking code with ruff..."
	@$(RUFF) check .
	@$(RUFF) format --check .
	@echo "✓ All checks passed"

lint-fix: venv ## Fix code issues with ruff (auto-fix + format)
	@echo "Fixing code issues with ruff..."
	@$(RUFF) check --fix .
	@$(RUFF) format .
	@echo "✓ Code fixed and formatted"

clean: ## Remove virtual environment and cache files
	rm -rf $(VENV)
	rm -rf .pytest_cache
	rm -rf __pycache__
	rm -rf .coverage
	rm -rf htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned up"

# Development shortcuts
.PHONY: dev-setup
dev-setup: venv ## Set up development environment
	@echo "✓ Development environment ready"
	@echo ""
	@echo "To activate the virtual environment:"
	@echo "  source $(VENV)/bin/activate"
	@echo ""
	@echo "To run tests:"
	@echo "  make test"
