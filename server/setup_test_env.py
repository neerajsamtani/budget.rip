#!/usr/bin/env python3
"""
Test Environment Setup Script
=============================

This script helps you set up a proper test environment for your Budgit application.

Run this script to:
1. Create a .env.test file with test-specific configuration
2. Verify your MongoDB connection
3. Set up the test database
"""

import sys
from pathlib import Path


def create_test_env_file():
    """Create a .env.test file with test configuration."""
    env_test_path = Path(".env.test")

    if env_test_path.exists():
        print("⚠️  .env.test already exists. Skipping creation.")
        return

    test_env_content = """# Test Environment Configuration
# This file contains test-specific environment variables

# Test Database URI - Use a separate database for testing
TEST_MONGO_URI=mongodb://localhost:27017/budgit_test

# Test JWT Secret (can be the same as production for simplicity)
JWT_SECRET_KEY=testSecretKey123

# Other test-specific environment variables can be added here
# Make sure to use test-specific values for any external services
"""

    with open(env_test_path, "w") as f:
        f.write(test_env_content)

    print("✅ Created .env.test file with test configuration")


def verify_mongodb_connection():
    """Verify that MongoDB is running and accessible."""
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure

        # Try to connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("✅ MongoDB connection successful")

        # Test creating the test database
        test_db = client["budgit_test"]
        test_collection = test_db["test_connection"]
        test_collection.insert_one({"test": "connection"})
        test_collection.delete_one({"test": "connection"})
        print("✅ Test database 'budgit_test' is accessible")

        client.close()
        return True

    except ConnectionFailure:
        print("❌ Failed to connect to MongoDB. Make sure MongoDB is running.")
        print("   Start MongoDB with: brew services start mongodb-community")
        return False
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        return False


def main():
    print("🚀 Setting up test environment for Budgit...")
    print()

    # Create test environment file
    create_test_env_file()
    print()

    # Verify MongoDB connection
    if not verify_mongodb_connection():
        print()
        print("❌ Test environment setup failed. Please fix the MongoDB connection and try again.")
        sys.exit(1)

    print()
    print("✅ Test environment setup complete!")
    print()
    print("Next steps:")
    print("1. Run your tests with: python -m pytest tests/ -v")
    print("2. The tests will now use the 'budgit_test' database instead of your production database")
    print("3. Collections will be automatically cleaned up between tests")


if __name__ == "__main__":
    main()
