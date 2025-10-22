#!/usr/bin/env python3
"""
Phase 2: Migrate Reference Data from MongoDB to PostgreSQL

This script migrates:
1. Categories
2. Payment methods
3. Parties
4. Tags

Usage:
    python migrations/phase2_migrate_reference_data.py
"""

import sys
from datetime import datetime, UTC
from typing import Dict, Optional, List, Any
from pymongo import MongoClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import text

sys.path.insert(0, '.')
from constants import MONGO_URI, CATEGORIES
from models.database import SessionLocal, engine
from models.sql_models import Category, PaymentMethod, Party, Tag
from utils.id_generator import generate_id


def migrate_categories(mongo_db, sql_db: Session) -> Dict[str, str]:
    """
    Migrate categories from MongoDB to PostgreSQL.

    Returns:
        Dict mapping category names to PostgreSQL IDs
    """
    print("\n=== Migrating Categories ===")

    # MongoDB stores categories as a simple list in the codebase constants
    # We'll use the CATEGORIES constant to populate the database
    category_map = {}
    migrated = 0
    skipped = 0

    for category_name in CATEGORIES:
        try:
            # Check if category already exists
            existing = sql_db.query(Category).filter(Category.name == category_name).first()
            if existing:
                category_map[category_name] = existing.id
                skipped += 1
                continue

            # Create new category
            category = Category(
                id=generate_id("cat"),
                name=category_name,
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            sql_db.add(category)
            sql_db.commit()

            category_map[category_name] = category.id
            migrated += 1
            print(f"  ✓ Migrated category: {category_name} -> {category.id}")

        except IntegrityError as e:
            sql_db.rollback()
            print(f"  ✗ Duplicate category: {category_name}")
            # Get existing ID
            existing = sql_db.query(Category).filter(Category.name == category_name).first()
            if existing:
                category_map[category_name] = existing.id
            skipped += 1
        except Exception as e:
            sql_db.rollback()
            print(f"  ✗ Error migrating category {category_name}: {e}")

    print(f"\nCategories: {migrated} migrated, {skipped} skipped")
    return category_map


def migrate_payment_methods(mongo_db, sql_db: Session) -> Dict[str, str]:
    """
    Migrate payment methods from MongoDB to PostgreSQL.

    Returns:
        Dict mapping payment method names to PostgreSQL IDs
    """
    print("\n=== Migrating Payment Methods ===")

    payment_method_map = {}
    migrated = 0
    skipped = 0

    try:
        payment_methods = list(mongo_db.payment_methods.find())
    except Exception as e:
        print(f"  ✗ Error accessing MongoDB payment_methods collection: {e}")
        print("  Creating default payment methods instead...")
        payment_methods = []

    # If no payment methods in MongoDB, create some defaults
    if not payment_methods:
        payment_methods = [
            {"name": "Cash", "type": "cash"},
            {"name": "Venmo", "type": "venmo"},
            {"name": "Splitwise", "type": "splitwise"},
        ]

    for pm_doc in payment_methods:
        try:
            pm_name = pm_doc.get("name")
            if not pm_name:
                continue

            # Check if payment method already exists
            existing = sql_db.query(PaymentMethod).filter(PaymentMethod.name == pm_name).first()
            if existing:
                payment_method_map[pm_name] = existing.id
                skipped += 1
                continue

            # Determine payment method type
            pm_type = pm_doc.get("type", "credit")
            if pm_type not in ["bank", "credit", "venmo", "splitwise", "cash"]:
                # Try to infer type from name
                name_lower = pm_name.lower()
                if "venmo" in name_lower:
                    pm_type = "venmo"
                elif "splitwise" in name_lower:
                    pm_type = "splitwise"
                elif "cash" in name_lower:
                    pm_type = "cash"
                elif "checking" in name_lower or "savings" in name_lower:
                    pm_type = "bank"
                else:
                    pm_type = "credit"

            # Create new payment method
            payment_method = PaymentMethod(
                id=generate_id("pm"),
                name=pm_name,
                type=pm_type,
                external_id=pm_doc.get("external_id"),
                is_active=pm_doc.get("is_active", True),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            sql_db.add(payment_method)
            sql_db.commit()

            payment_method_map[pm_name] = payment_method.id
            migrated += 1
            print(f"  ✓ Migrated payment method: {pm_name} ({pm_type}) -> {payment_method.id}")

        except IntegrityError:
            sql_db.rollback()
            print(f"  ✗ Duplicate payment method: {pm_name}")
            existing = sql_db.query(PaymentMethod).filter(PaymentMethod.name == pm_name).first()
            if existing:
                payment_method_map[pm_name] = existing.id
            skipped += 1
        except Exception as e:
            sql_db.rollback()
            print(f"  ✗ Error migrating payment method {pm_name}: {e}")

    print(f"\nPayment Methods: {migrated} migrated, {skipped} skipped")
    return payment_method_map


def migrate_parties(mongo_db, sql_db: Session) -> Dict[str, str]:
    """
    Migrate parties from MongoDB to PostgreSQL.
    Parties are extracted from line items or from a dedicated collection.

    Returns:
        Dict mapping party names to PostgreSQL IDs
    """
    print("\n=== Migrating Parties ===")

    party_map = {}
    migrated = 0
    skipped = 0

    # Try to get unique parties from line items
    unique_parties = set()

    try:
        # Get unique parties from line items
        line_items = list(mongo_db.line_items.find())
        for item in line_items:
            party = item.get("party")
            if party and isinstance(party, str) and party.strip():
                unique_parties.add(party.strip())
    except Exception as e:
        print(f"  ✗ Error accessing MongoDB line_items collection: {e}")

    # Also check if there's a dedicated parties collection
    try:
        parties = list(mongo_db.parties.find())
        for party_doc in parties:
            party_name = party_doc.get("name")
            if party_name:
                unique_parties.add(party_name)
    except Exception as e:
        pass  # It's okay if there's no parties collection

    if not unique_parties:
        print("  No parties found to migrate")
        return party_map

    for party_name in sorted(unique_parties):
        try:
            # Check if party already exists
            existing = sql_db.query(Party).filter(Party.name == party_name).first()
            if existing:
                party_map[party_name] = existing.id
                skipped += 1
                continue

            # Create new party
            party = Party(
                id=generate_id("party"),
                name=party_name,
                is_ignored=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            sql_db.add(party)
            sql_db.commit()

            party_map[party_name] = party.id
            migrated += 1
            print(f"  ✓ Migrated party: {party_name} -> {party.id}")

        except IntegrityError:
            sql_db.rollback()
            print(f"  ✗ Duplicate party: {party_name}")
            existing = sql_db.query(Party).filter(Party.name == party_name).first()
            if existing:
                party_map[party_name] = existing.id
            skipped += 1
        except Exception as e:
            sql_db.rollback()
            print(f"  ✗ Error migrating party {party_name}: {e}")

    print(f"\nParties: {migrated} migrated, {skipped} skipped")
    return party_map


def migrate_tags(mongo_db, sql_db: Session) -> Dict[str, str]:
    """
    Migrate tags from MongoDB to PostgreSQL.
    Tags are extracted from events.

    Returns:
        Dict mapping tag names to PostgreSQL IDs
    """
    print("\n=== Migrating Tags ===")

    tag_map = {}
    migrated = 0
    skipped = 0

    # Get unique tags from events
    unique_tags = set()

    try:
        events = list(mongo_db.events.find())
        for event in events:
            tags = event.get("tags", [])
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, str) and tag.strip():
                        unique_tags.add(tag.strip())
    except Exception as e:
        print(f"  ✗ Error accessing MongoDB events collection: {e}")

    if not unique_tags:
        print("  No tags found to migrate")
        return tag_map

    for tag_name in sorted(unique_tags):
        try:
            # Check if tag already exists
            existing = sql_db.query(Tag).filter(Tag.name == tag_name).first()
            if existing:
                tag_map[tag_name] = existing.id
                skipped += 1
                continue

            # Create new tag
            tag = Tag(
                id=generate_id("tag"),
                name=tag_name,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            sql_db.add(tag)
            sql_db.commit()

            tag_map[tag_name] = tag.id
            migrated += 1
            print(f"  ✓ Migrated tag: {tag_name} -> {tag.id}")

        except IntegrityError:
            sql_db.rollback()
            print(f"  ✗ Duplicate tag: {tag_name}")
            existing = sql_db.query(Tag).filter(Tag.name == tag_name).first()
            if existing:
                tag_map[tag_name] = existing.id
            skipped += 1
        except Exception as e:
            sql_db.rollback()
            print(f"  ✗ Error migrating tag {tag_name}: {e}")

    print(f"\nTags: {migrated} migrated, {skipped} skipped")
    return tag_map


def main():
    """Run Phase 2 migration."""
    print("=" * 60)
    print("Phase 2: Migrating Reference Data")
    print("=" * 60)

    # Connect to MongoDB
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_db = mongo_client.get_database()
        # Test connection
        mongo_client.server_info()
        print(f"\n✓ Connected to MongoDB: {MONGO_URI}")
    except Exception as e:
        print(f"\n✗ Error connecting to MongoDB: {e}")
        print("  Migration will use default/fallback data where possible")
        mongo_db = None

    # Connect to PostgreSQL
    sql_db = SessionLocal()

    try:
        # Test PostgreSQL connection
        sql_db.execute(text("SELECT 1"))
        print(f"✓ Connected to PostgreSQL")

        # Run migrations
        category_map = migrate_categories(mongo_db, sql_db)
        payment_method_map = migrate_payment_methods(mongo_db, sql_db)
        party_map = migrate_parties(mongo_db, sql_db)
        tag_map = migrate_tags(mongo_db, sql_db)

        # Summary
        print("\n" + "=" * 60)
        print("Migration Summary")
        print("=" * 60)
        print(f"Categories:       {len(category_map)} total")
        print(f"Payment Methods:  {len(payment_method_map)} total")
        print(f"Parties:          {len(party_map)} total")
        print(f"Tags:             {len(tag_map)} total")
        print("=" * 60)
        print("✓ Phase 2 migration completed successfully!")

    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        sql_db.close()
        if mongo_db:
            mongo_client.close()


if __name__ == "__main__":
    main()
