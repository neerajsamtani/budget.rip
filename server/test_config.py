"""
Test Configuration
==================

This file contains test-specific configuration settings.

To use a separate test database:

1. Set the TEST_MONGO_URI environment variable:
   export TEST_MONGO_URI="mongodb://localhost:27017/budgit_test"

2. Or create a .env.test file with:
   TEST_MONGO_URI=mongodb://localhost:27017/budgit_test

3. Run tests with:
   python -m pytest tests/ -v

The test database will be automatically created and cleaned up between tests.
"""

import os

from dotenv import load_dotenv

# Load test environment variables if .env.test exists
if os.path.exists(".env.test"):
    load_dotenv(".env.test")

# Test database configuration
TEST_MONGO_URI = os.getenv("TEST_MONGO_URI", "mongodb://localhost:27017/budgit_test")
TEST_DB_NAME = "budgit_test"

# Test JWT configuration
TEST_JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "testSecretKey123")
