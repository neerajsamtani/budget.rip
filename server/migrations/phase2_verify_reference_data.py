#!/usr/bin/env python3
"""
Phase 2: Verification Script for Reference Data Migration

This script verifies that reference data was correctly migrated from MongoDB to PostgreSQL.

Usage:
    python migrations/phase2_verify_reference_data.py
"""

import sys
from pymongo import MongoClient
from sqlalchemy import text

sys.path.insert(0, '.')
from constants import MONGO_URI, CATEGORIES
from models.database import SessionLocal, engine
from models.sql_models import Category, PaymentMethod, Party, Tag


def verify_categories(mongo_db, sql_db):
    """Verify categories migration."""
    print("\n=== Verifying Categories ===")

    # Get PostgreSQL count
    pg_count = sql_db.query(Category).count()
    print(f"PostgreSQL categories: {pg_count}")

    # At minimum, we should have the categories from CATEGORIES constant
    expected_min = len(CATEGORIES)
    print(f"Expected minimum:      {expected_min}")

    errors = []

    # Check that all CATEGORIES exist in PostgreSQL
    for cat_name in CATEGORIES:
        exists = sql_db.query(Category).filter(Category.name == cat_name).first()
        if not exists:
            errors.append(f"Missing category in PostgreSQL: {cat_name}")

    # Check for duplicates
    duplicates = sql_db.execute(text("""
        SELECT name, COUNT(*) as count
        FROM categories
        GROUP BY name
        HAVING COUNT(*) > 1
    """)).fetchall()

    if duplicates:
        for dup in duplicates:
            errors.append(f"Duplicate category: {dup[0]} (appears {dup[1]} times)")

    # Check ID format
    invalid_ids = sql_db.query(Category).filter(~Category.id.like('cat_%')).all()
    for cat in invalid_ids:
        errors.append(f"Invalid ID format for category {cat.name}: {cat.id}")

    # Check required fields
    missing_fields = sql_db.query(Category).filter(
        (Category.name == None) | (Category.name == '')
    ).all()
    if missing_fields:
        errors.append(f"{len(missing_fields)} categories missing name field")

    if errors:
        print("✗ FAILED - Errors found:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✓ PASSED - All categories verified")
        return True


def verify_payment_methods(mongo_db, sql_db):
    """Verify payment methods migration."""
    print("\n=== Verifying Payment Methods ===")

    # Get PostgreSQL count
    pg_count = sql_db.query(PaymentMethod).count()
    print(f"PostgreSQL payment methods: {pg_count}")

    errors = []

    # Check for duplicates
    duplicates = sql_db.execute(text("""
        SELECT name, COUNT(*) as count
        FROM payment_methods
        GROUP BY name
        HAVING COUNT(*) > 1
    """)).fetchall()

    if duplicates:
        for dup in duplicates:
            errors.append(f"Duplicate payment method: {dup[0]} (appears {dup[1]} times)")

    # Check ID format
    invalid_ids = sql_db.query(PaymentMethod).filter(~PaymentMethod.id.like('pm_%')).all()
    for pm in invalid_ids:
        errors.append(f"Invalid ID format for payment method {pm.name}: {pm.id}")

    # Check required fields
    missing_fields = sql_db.query(PaymentMethod).filter(
        (PaymentMethod.name == None) | (PaymentMethod.name == '') |
        (PaymentMethod.type == None)
    ).all()
    if missing_fields:
        errors.append(f"{len(missing_fields)} payment methods missing required fields")

    # Check type values
    invalid_types = sql_db.execute(text("""
        SELECT id, name, type
        FROM payment_methods
        WHERE type NOT IN ('bank', 'credit', 'venmo', 'splitwise', 'cash')
    """)).fetchall()
    if invalid_types:
        for pm in invalid_types:
            errors.append(f"Invalid type for payment method {pm[1]}: {pm[2]}")

    if errors:
        print("✗ FAILED - Errors found:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✓ PASSED - All payment methods verified")
        return True


def verify_parties(mongo_db, sql_db):
    """Verify parties migration."""
    print("\n=== Verifying Parties ===")

    # Get PostgreSQL count
    pg_count = sql_db.query(Party).count()
    print(f"PostgreSQL parties: {pg_count}")

    errors = []

    # Check for duplicates
    duplicates = sql_db.execute(text("""
        SELECT name, COUNT(*) as count
        FROM parties
        GROUP BY name
        HAVING COUNT(*) > 1
    """)).fetchall()

    if duplicates:
        for dup in duplicates:
            errors.append(f"Duplicate party: {dup[0]} (appears {dup[1]} times)")

    # Check ID format
    invalid_ids = sql_db.query(Party).filter(~Party.id.like('party_%')).all()
    for party in invalid_ids:
        errors.append(f"Invalid ID format for party {party.name}: {party.id}")

    # Check required fields
    missing_fields = sql_db.query(Party).filter(
        (Party.name == None) | (Party.name == '')
    ).all()
    if missing_fields:
        errors.append(f"{len(missing_fields)} parties missing name field")

    if errors:
        print("✗ FAILED - Errors found:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✓ PASSED - All parties verified")
        return True


def verify_tags(mongo_db, sql_db):
    """Verify tags migration."""
    print("\n=== Verifying Tags ===")

    # Get PostgreSQL count
    pg_count = sql_db.query(Tag).count()
    print(f"PostgreSQL tags: {pg_count}")

    errors = []

    # Check for duplicates
    duplicates = sql_db.execute(text("""
        SELECT name, COUNT(*) as count
        FROM tags
        GROUP BY name
        HAVING COUNT(*) > 1
    """)).fetchall()

    if duplicates:
        for dup in duplicates:
            errors.append(f"Duplicate tag: {dup[0]} (appears {dup[1]} times)")

    # Check ID format
    invalid_ids = sql_db.query(Tag).filter(~Tag.id.like('tag_%')).all()
    for tag in invalid_ids:
        errors.append(f"Invalid ID format for tag {tag.name}: {tag.id}")

    # Check required fields
    missing_fields = sql_db.query(Tag).filter(
        (Tag.name == None) | (Tag.name == '')
    ).all()
    if missing_fields:
        errors.append(f"{len(missing_fields)} tags missing name field")

    if errors:
        print("✗ FAILED - Errors found:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✓ PASSED - All tags verified")
        return True


def main():
    """Run Phase 2 verification."""
    print("=" * 60)
    print("Phase 2: Verifying Reference Data Migration")
    print("=" * 60)

    # Connect to MongoDB
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_db = mongo_client.get_database()
        mongo_client.server_info()
        print(f"\n✓ Connected to MongoDB: {MONGO_URI}")
    except Exception as e:
        print(f"\n⚠ Warning: Could not connect to MongoDB: {e}")
        print("  Will verify PostgreSQL data integrity only")
        mongo_db = None

    # Connect to PostgreSQL
    sql_db = SessionLocal()

    try:
        # Test PostgreSQL connection
        sql_db.execute(text("SELECT 1"))
        print(f"✓ Connected to PostgreSQL")

        # Run verifications
        results = []
        results.append(("Categories", verify_categories(mongo_db, sql_db)))
        results.append(("Payment Methods", verify_payment_methods(mongo_db, sql_db)))
        results.append(("Parties", verify_parties(mongo_db, sql_db)))
        results.append(("Tags", verify_tags(mongo_db, sql_db)))

        # Summary
        print("\n" + "=" * 60)
        print("Verification Summary")
        print("=" * 60)

        all_passed = True
        for name, passed in results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{name:20} {status}")
            if not passed:
                all_passed = False

        print("=" * 60)

        if all_passed:
            print("✓ All verifications passed!")
            sys.exit(0)
        else:
            print("✗ Some verifications failed - please review errors above")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        sql_db.close()
        if mongo_db:
            mongo_client.close()


if __name__ == "__main__":
    main()
