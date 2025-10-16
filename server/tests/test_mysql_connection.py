#!/usr/bin/env python
"""
Test MySQL connection and SQLAlchemy models.

This module verifies:
1. Database connection is working (SELECT 1)
2. SQLAlchemy models can create records
3. Transactions commit successfully
4. Records can be queried
5. Records can be deleted

Run with: pytest tests/test_mysql_connection.py
"""

import pytest
from sqlalchemy import text

from models.database import db_session, engine
from models.sql_models import Category
from utils.id_generator import generate_id


def test_basic_connection():
    """Test basic database connection with SELECT 1"""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

        assert value == 1, f"Expected SELECT 1 to return 1, got {value}"
        assert engine.url is not None, "Database URL should not be None"


def test_table_existence():
    """Verify all expected tables exist in the database"""
    expected_tables = [
        "categories",
        "payment_methods",
        "parties",
        "tags",
        "transactions",
        "line_items",
        "events",
        "event_line_items",
        "event_tags",
        "alembic_version",
    ]

    with engine.connect() as connection:
        result = connection.execute(text("SHOW TABLES"))
        actual_tables = [row[0] for row in result]

        missing_tables = set(expected_tables) - set(actual_tables)
        assert not missing_tables, f"Missing tables: {', '.join(missing_tables)}"

        for expected_table in expected_tables:
            assert expected_table in actual_tables, f"Expected table '{expected_table}' not found"


def test_category_crud():
    """Test creating, reading, and deleting a Category"""
    session = db_session()
    test_category_id = generate_id("cat")

    try:
        # Create a test category
        test_category = Category(
            id=test_category_id,
            name="TEST_CATEGORY_DO_NOT_USE",
            is_active=True
        )
        session.add(test_category)
        session.commit()

        # Query to verify it exists
        queried_category = (
            session.query(Category).filter(Category.id == test_category_id).first()
        )
        assert queried_category is not None, "Category not found after creation"
        assert queried_category.name == "TEST_CATEGORY_DO_NOT_USE"
        assert queried_category.is_active is True
        assert queried_category.created_at is not None

        # Delete the test category
        session.delete(queried_category)
        session.commit()

        # Verify it's gone
        deleted_check = (
            session.query(Category).filter(Category.id == test_category_id).first()
        )
        assert deleted_check is None, "Category still exists after deletion"

    finally:
        # Cleanup: Try to delete the test category if it still exists
        try:
            cleanup = (
                session.query(Category)
                .filter(Category.id == test_category_id)
                .first()
            )
            if cleanup:
                session.delete(cleanup)
                session.commit()
        except Exception:
            pass

        session.close()
