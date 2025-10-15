#!/usr/bin/env python
"""
Test MySQL connection and SQLAlchemy models.

This script verifies:
1. Database connection is working (SELECT 1)
2. SQLAlchemy models can create records
3. Transactions commit successfully
4. Records can be queried
5. Records can be deleted

Run with: python test_mysql_connection.py
"""

from sqlalchemy import text
from models.database import engine, db_session
from models.sql_models import Category
from utils.id_generator import generate_id


def test_basic_connection():
    """Test basic database connection with SELECT 1"""
    print("=" * 60)
    print("TEST 1: Basic Database Connection")
    print("=" * 60)

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()

            if value == 1:
                print("✓ Database connection successful")
                print(f"✓ Connected to: {engine.url}")
                return True
            else:
                print(f"✗ Unexpected result from SELECT 1: {value}")
                return False
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def test_category_crud():
    """Test creating, reading, and deleting a Category"""
    print("\n" + "=" * 60)
    print("TEST 2: Category Model CRUD Operations")
    print("=" * 60)

    session = db_session()
    test_category_id = None

    try:
        # Step 1: Create a test category
        print("\n1. Creating test Category...")
        test_category_id = generate_id("cat")
        test_category = Category(
            id=test_category_id,
            name="TEST_CATEGORY_DO_NOT_USE",
            is_active=True
        )

        session.add(test_category)
        session.commit()
        print(f"✓ Category created with ID: {test_category_id}")

        # Step 2: Query to verify it exists
        print("\n2. Querying for created Category...")
        queried_category = session.query(Category).filter(
            Category.id == test_category_id
        ).first()

        if queried_category:
            print(f"✓ Category found: {queried_category.name}")
            print(f"  - ID: {queried_category.id}")
            print(f"  - Name: {queried_category.name}")
            print(f"  - Active: {queried_category.is_active}")
            print(f"  - Created at: {queried_category.created_at}")
        else:
            print("✗ Category not found after creation")
            return False

        # Step 3: Delete the test category
        print("\n3. Deleting test Category...")
        session.delete(queried_category)
        session.commit()
        print("✓ Category deleted")

        # Step 4: Verify it's gone
        print("\n4. Verifying Category was deleted...")
        deleted_check = session.query(Category).filter(
            Category.id == test_category_id
        ).first()

        if deleted_check is None:
            print("✓ Category successfully removed from database")
            return True
        else:
            print("✗ Category still exists after deletion")
            return False

    except Exception as e:
        print(f"✗ Error during Category CRUD test: {e}")
        session.rollback()

        # Cleanup: Try to delete the test category if it exists
        if test_category_id:
            try:
                cleanup = session.query(Category).filter(
                    Category.id == test_category_id
                ).first()
                if cleanup:
                    session.delete(cleanup)
                    session.commit()
                    print(f"✓ Cleaned up test category: {test_category_id}")
            except:
                pass

        return False
    finally:
        session.close()


def test_table_existence():
    """Verify all expected tables exist in the database"""
    print("\n" + "=" * 60)
    print("TEST 3: Database Tables")
    print("=" * 60)

    expected_tables = [
        'categories',
        'payment_methods',
        'parties',
        'tags',
        'transactions',
        'line_items',
        'events',
        'event_line_items',
        'event_tags',
        'alembic_version'
    ]

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SHOW TABLES"))
            actual_tables = [row[0] for row in result]

            print(f"\nFound {len(actual_tables)} tables:")
            for table in sorted(actual_tables):
                status = "✓" if table in expected_tables else "?"
                print(f"  {status} {table}")

            missing_tables = set(expected_tables) - set(actual_tables)
            if missing_tables:
                print(f"\n✗ Missing tables: {', '.join(missing_tables)}")
                return False
            else:
                print("\n✓ All expected tables exist")
                return True

    except Exception as e:
        print(f"✗ Error checking tables: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MySQL Connection and Model Tests")
    print("=" * 60)

    results = []

    # Test 1: Basic connection
    results.append(("Basic Connection", test_basic_connection()))

    # Test 2: Table existence
    results.append(("Table Existence", test_table_existence()))

    # Test 3: Category CRUD
    results.append(("Category CRUD", test_category_crud()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED - MySQL is ready for migration!")
    else:
        print("✗ SOME TESTS FAILED - Please review errors above")
    print("=" * 60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
