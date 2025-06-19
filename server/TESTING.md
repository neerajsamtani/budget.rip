# Testing Guide

This document explains how to set up and run tests for the Budgit server application.

## Test Environment Setup

The tests are configured to use a separate test database to avoid affecting your production data.

### Quick Setup

1. **Run the setup script** (recommended):
   ```bash
   python setup_test_env.py
   ```

2. **Or manually create a `.env.test` file**:
   ```bash
   # Test Database URI - Use a separate database for testing
   TEST_MONGO_URI=mongodb://localhost:27017/budgit_test
   
   # Test JWT Secret
   JWT_SECRET_KEY=testSecretKey123
   ```

### Prerequisites

- MongoDB running locally (or accessible via the configured URI)
- Python dependencies installed (`pip install -r requirements.txt`)

## Running Tests

### Run all tests:
```bash
python -m pytest tests/ -v
```

### Run specific test files:
```bash
python -m pytest tests/test_cash.py -v
python -m pytest tests/test_dao.py -v
python -m pytest tests/test_helpers.py -v
```

### Run specific test functions:
```bash
python -m pytest tests/test_cash.py::test_create_cash_transaction_api -v
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