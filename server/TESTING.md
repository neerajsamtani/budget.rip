# Testing Guide

This document explains how to set up and run tests for the Budgit server application.

## Quick Start (Recommended)

The easiest way to run tests is using Make commands, which automatically handle virtual environment setup and dependency management:

```bash
# Run all tests
make test

# Run only Phase 3 migration tests
make test-phase3

# Run tests with coverage report
make test-coverage

# See all available commands
make help
```

The Makefile will:
- ✅ Create a virtual environment (if needed)
- ✅ Install/update dependencies automatically
- ✅ Run tests in an isolated environment
- ✅ Avoid system package conflicts

## Test Environment Setup

The tests are configured to use:
- **mongomock** for MongoDB tests (no MongoDB server needed)
- **SQLite in-memory** for PostgreSQL/SQLAlchemy tests (no PostgreSQL server needed)
- **Virtual environment** to avoid dependency conflicts
- **pyproject.toml** for pytest and coverage configuration

### Prerequisites

- Python 3.11+
- Make (for convenience commands)
- No external databases required (uses mocks)

### Configuration

Test configuration is defined in `pyproject.toml`:
- **pytest settings**: Test discovery, markers, output options
- **coverage settings**: Source paths, exclusions, reporting format

This follows modern Python best practices (PEP 518/621) while keeping dependencies in `requirements.txt` for this legacy Flask app.

### Manual Setup (Advanced)

If you prefer to set up the environment manually:

1. **Create virtual environment**:
   ```bash
   python3 -m venv test_env
   source test_env/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run tests**:
   ```bash
   python -m pytest tests/ -v
   ```

## Running Tests

### Using Make (recommended):
```bash
make test                         # All tests
make test-phase3                  # Phase 3 migration tests only
make test-coverage                # Tests with coverage report
make test-quick                   # Quick run without verbose output
make help                         # See all available commands
```

### Using pytest directly (advanced):
```bash
# Activate virtual environment first
source test_env/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_cash.py -v
pytest tests/test_phase3_migration.py -v

# Run specific test functions
pytest tests/test_cash.py::test_create_cash_transaction_api -v

# Run with custom options
pytest tests/ -v -k "venmo" --maxfail=1
```

## Test Database

- **Database Name**: `budgit_test`
- **Collections**: All collections are automatically cleaned up between tests
- **Isolation**: Tests use a completely separate database from your production data

## Test Configuration

The test configuration is handled by:

1. **`tests/conftest.py`**: Main test configuration and fixtures
2. **`test_config.py`**: Test-specific configuration settings
3. **`.env.test`**: Environment variables for testing

## Key Features

- ✅ **Database Isolation**: Tests use a separate `budgit_test` database
- ✅ **Automatic Cleanup**: Collections are dropped before and after each test
- ✅ **JWT Authentication**: Test JWT tokens are automatically generated
- ✅ **Flask Test Client**: Full Flask application context for integration tests

## Troubleshooting

### MongoDB Connection Issues
If you get connection errors:
```bash
# Start MongoDB (macOS with Homebrew)
brew services start mongodb-community

# Or start manually
mongod --dbpath /usr/local/var/mongodb
```

### Test Database Issues
If tests are still writing to production database:
1. Check that `TEST_MONGO_URI` is set correctly in `.env.test`
2. Verify that `dao.py` is using the configured database name
3. Ensure your tests are importing from the updated `conftest.py`

### Permission Issues
If you can't create the test database:
```bash
# Check MongoDB permissions
mongo --eval "db.createUser({user: 'testuser', pwd: 'testpass', roles: ['readWrite']})"
```

## Test Structure

```
tests/
├── conftest.py          # Test configuration and fixtures
├── test_cash.py         # Cash-related API tests
├── test_dao.py          # Data access object tests
└── test_helpers.py      # Utility function tests
```

## Adding New Tests

1. Create test files in the `tests/` directory
2. Use the fixtures from `conftest.py`:
   - `flask_app`: Flask application with test configuration
   - `test_client`: Flask test client for API testing
   - `jwt_token`: JWT token for authenticated requests
   - `setup_teardown`: Automatic database cleanup

Example:
```python
def test_my_function(flask_app, test_client, jwt_token):
    with flask_app.app_context():
        # Your test code here
        pass
``` 