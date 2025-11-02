#!/usr/bin/env python
"""
Phase 2 Migration: Categories

Migrates categories from the CATEGORIES constant in constants.py to PostgreSQL.

Since categories don't exist in MongoDB, we create them from the hardcoded list.
Note: We skip "All" as it's a filter category, not a real transaction category.

Usage:
    python migrations/phase2_migrate_categories.py
"""

import sys
import os

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from sqlalchemy.exc import IntegrityError
from datetime import datetime, UTC

from constants import CATEGORIES
from models.database import SessionLocal
from models.sql_models import Category
from utils.id_generator import generate_id

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def migrate_categories():
    """
    Migrate categories from CATEGORIES constant to PostgreSQL.

    Returns:
        dict: Mapping of category name to PostgreSQL ID
    """
    db = SessionLocal()
    category_map = {}

    try:
        # Filter out "All" - it's a UI filter, not a real category
        actual_categories = [cat for cat in CATEGORIES if cat != "All"]

        logger.info(f"Starting migration of {len(actual_categories)} categories...")
        logger.info(f"Categories to migrate: {actual_categories}")

        migrated_count = 0
        skipped_count = 0

        for category_name in actual_categories:
            try:
                # Check if category already exists
                existing = (
                    db.query(Category).filter(Category.name == category_name).first()
                )

                if existing:
                    logger.info(
                        f"  ⊙ Category already exists: {category_name} -> {existing.id}"
                    )
                    category_map[category_name] = existing.id
                    skipped_count += 1
                    continue

                # Create new category
                category = Category(
                    id=generate_id("cat"),
                    name=category_name,
                    is_active=True,
                    mongo_id=None,  # Categories don't exist in MongoDB
                )

                db.add(category)
                db.flush()  # Get ID without committing

                category_map[category_name] = category.id
                logger.info(f"  ✓ Migrated: {category_name} -> {category.id}")
                migrated_count += 1

            except IntegrityError as e:
                logger.warning(f"  ! Integrity error for {category_name}: {e}")
                db.rollback()

                # Try to get the existing record
                existing = (
                    db.query(Category).filter(Category.name == category_name).first()
                )
                if existing:
                    category_map[category_name] = existing.id
                    skipped_count += 1

            except Exception as e:
                logger.error(f"  ✗ Error migrating {category_name}: {e}")
                db.rollback()
                raise

        # Commit all changes
        db.commit()

        logger.info(f"\n✅ Category migration complete!")
        logger.info(f"   Migrated: {migrated_count}")
        logger.info(f"   Skipped (already exist): {skipped_count}")
        logger.info(f"   Total in map: {len(category_map)}")

        return category_map

    except Exception as e:
        logger.error(f"\n❌ Category migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_migration():
    """Verify that all categories were migrated correctly."""
    db = SessionLocal()
    try:
        actual_categories = [cat for cat in CATEGORIES if cat != "All"]
        db_categories = db.query(Category).all()

        logger.info(f"\n📊 Verification:")
        logger.info(f"   Expected categories: {len(actual_categories)}")
        logger.info(f"   PostgreSQL categories: {len(db_categories)}")

        # Check for missing categories
        db_category_names = {cat.name for cat in db_categories}
        missing = set(actual_categories) - db_category_names

        if missing:
            logger.warning(f"   ⚠️  Missing categories: {missing}")
            return False

        logger.info(f"   ✓ All categories present")

        # Show all categories
        logger.info(f"\n   Categories in PostgreSQL:")
        for cat in sorted(db_categories, key=lambda x: x.name):
            logger.info(f"     • {cat.name} ({cat.id}) - active: {cat.is_active}")

        return True

    finally:
        db.close()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Phase 2: Migrate Categories")
    logger.info("=" * 60)

    # Run migration
    category_map = migrate_categories()

    # Verify
    success = verify_migration()

    if success:
        logger.info(f"\n✅ Phase 2 (Categories) completed successfully!\n")
        sys.exit(0)
    else:
        logger.error(f"\n❌ Phase 2 (Categories) verification failed!\n")
        sys.exit(1)
