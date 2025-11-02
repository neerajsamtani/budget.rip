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
- **SQLite shared in-memory** for PostgreSQL/SQLAlchemy tests (no PostgreSQL server needed)
  - Uses `sqlite:///file:memdb1?mode=memory&cache=shared&uri=true` to allow multiple connections to share the same database
  - This ensures dual-write operations and test fixtures access the same database instance
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
   python3 -m venv env
   source env/bin/activate
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
source env/bin/activate

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

## Test Database Isolation

**CRITICAL**: Tests are completely isolated from production databases.

### MongoDB
- **Implementation**: `mongomock` (in-memory fake MongoDB)
- **No server required**: Tests don't connect to real MongoDB
- **Automatic cleanup**: Collections dropped before/after each test

### PostgreSQL
- **Implementation**: SQLite in-memory (`sqlite:///:memory:`)
- **No server required**: Tests don't connect to real PostgreSQL
- **Configuration**: `DATABASE_URL` automatically set in `tests/conftest.py` before imports
- **Schema management**: Tables created/destroyed for each test
- **Complete isolation**: Production database never touched

### How It Works
```python
# In tests/conftest.py (executed before any imports)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"  # Override production PostgreSQL

# Later in the file
test_engine = create_engine(TEST_DATABASE_URL)  # SQLite in-memory
Base.metadata.create_all(test_engine)  # Create schema
```

## Test Configuration

The test configuration is handled by:

1. **`tests/conftest.py`**: Main test configuration and fixtures
   - Sets `DATABASE_URL` to SQLite before imports
   - Provides `mongomock` for MongoDB tests
   - Creates/destroys PostgreSQL schema per test
   - Provides Flask app and test client fixtures
2. **`pyproject.toml`**: pytest and coverage settings
3. **Environment variables**: Automatically configured in conftest

## Key Features

- ✅ **Complete Database Isolation**: Tests never touch production MongoDB or PostgreSQL
- ✅ **No External Dependencies**: No database servers needed
- ✅ **Automatic Cleanup**: All data cleaned between tests
- ✅ **JWT Authentication**: Test JWT tokens automatically generated
- ✅ **Flask Test Client**: Full Flask application context for integration tests
- ✅ **Fast Execution**: In-memory databases for speed

## Troubleshooting

### Tests Failing to Run
If pytest can't find tests or modules:
```bash
# Ensure you're in the server directory
cd server

# Activate virtual environment
source env/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v
```

### Import Errors
If you see import errors for `models.sql_models`:
```bash
# Make sure you're running from server directory with virtualenv active
cd server
source env/bin/activate
python -m pytest tests/ -v
```

### Test Data Pollution (FIXED)
**This issue is resolved** in the current implementation. If you suspect test data is polluting production:
1. Verify `tests/conftest.py` sets `os.environ["DATABASE_URL"] = "sqlite:///:memory:"` at the top
2. Check that this line executes **before** any imports of application code
3. Confirm tests are using the `flask_app` fixture (which uses the test config)

### Virtual Environment Issues
```bash
# Remove and recreate virtual environment
rm -rf env
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Test Structure

```
tests/
├── conftest.py                  # Test configuration and fixtures
│                                # - Database isolation setup
│                                # - Flask app and client fixtures
│                                # - Cleanup fixtures
├── test_phase3_migration.py     # Phase 3 migration tests
│                                # - Dual-write utility tests
│                                # - Transaction migration tests
│                                # - Line item migration tests
├── test_cash.py                 # Cash-related API tests
│   └── TestCashDualWrite        # Dual-write behavior tests
├── test_venmo.py                # Venmo API tests
│   └── TestVenmoDualWrite       # Dual-write behavior tests
├── test_splitwise.py            # Splitwise API tests
│   └── TestSplitwiseDualWrite   # Dual-write behavior tests
├── test_stripe.py               # Stripe API tests
│   └── TestStripeDualWrite      # Dual-write behavior tests
├── test_dao.py                  # Data access object tests
└── test_helpers.py              # Utility function tests
```

### Test Categories

1. **Migration Tests** (`test_phase3_migration.py`):
   - Dual-write utility functionality
   - Transaction and line item migration logic
   - Payment method lookup and creation

2. **Dual-Write Tests** (in each endpoint test file):
   - Verify `dual_write_operation()` is called
   - Check operation names are correct
   - Test MongoDB failure handling (should raise)
   - Test PostgreSQL failure handling (should log and continue)

3. **Integration Tests**:
   - End-to-end workflow tests
   - Full API request/response testing
   - Multi-step operations

4. **Unit Tests**:
   - Individual function testing
   - Helper function testing
   - DAO operations

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