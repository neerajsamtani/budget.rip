#!/usr/bin/env python
"""
Phase 2 Migration: Tags

Migrates tags from MongoDB events to PostgreSQL.

Tags are stored as string arrays on events in MongoDB (e.g., tags: ["Advika Trip", "Dubai"]).
This script extracts all unique tags and creates Tag records in PostgreSQL.

Usage:
    python migrations/phase2_migrate_tags.py
"""

import sys
import os

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from sqlalchemy.exc import IntegrityError
from pymongo import MongoClient

from constants import MONGO_URI
from models.database import SessionLocal
from models.sql_models import Tag
from utils.id_generator import generate_id

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def extract_unique_tags_from_mongodb():
    """
    Extract all unique tags from MongoDB events collection.

    Returns:
        set: Set of unique tag names
    """
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client["flask_db"]

    try:
        # Get all events that have tags
        events_with_tags = mongo_db.events.find(
            {"tags": {"$exists": True, "$ne": [], "$ne": None}}, {"tags": 1}
        )

        # Extract all unique tags
        all_tags = set()
        for event in events_with_tags:
            if event.get("tags"):
                all_tags.update(event["tags"])

        return all_tags
    finally:
        mongo_client.close()


def migrate_tags():
    """
    Migrate tags from MongoDB events to PostgreSQL.

    Returns:
        dict: Mapping of tag name to PostgreSQL ID
    """
    db = SessionLocal()
    tag_map = {}

    try:
        # Extract unique tags from MongoDB
        unique_tags = extract_unique_tags_from_mongodb()

        logger.info(f"Starting migration of {len(unique_tags)} tags...")
        logger.info(f"Tags to migrate: {sorted(unique_tags)}")

        migrated_count = 0
        skipped_count = 0

        for tag_name in sorted(unique_tags):
            try:
                # Check if tag already exists
                existing = db.query(Tag).filter(Tag.name == tag_name).first()

                if existing:
                    logger.info(f"  ⊙ Tag already exists: {tag_name} -> {existing.id}")
                    tag_map[tag_name] = existing.id
                    skipped_count += 1
                    continue

                # Create new tag
                tag = Tag(id=generate_id("tag"), name=tag_name)

                db.add(tag)
                db.flush()  # Get ID without committing

                tag_map[tag_name] = tag.id
                logger.info(f"  ✓ Migrated: {tag_name} -> {tag.id}")
                migrated_count += 1

            except IntegrityError as e:
                logger.warning(f"  ! Integrity error for {tag_name}: {e}")
                db.rollback()

                # Try to get the existing record
                existing = db.query(Tag).filter(Tag.name == tag_name).first()
                if existing:
                    tag_map[tag_name] = existing.id
                    skipped_count += 1

            except Exception as e:
                logger.error(f"  ✗ Error migrating {tag_name}: {e}")
                db.rollback()
                raise

        # Commit all changes
        db.commit()

        logger.info(f"\n✅ Tag migration complete!")
        logger.info(f"   Migrated: {migrated_count}")
        logger.info(f"   Skipped (already exist): {skipped_count}")
        logger.info(f"   Total in map: {len(tag_map)}")

        return tag_map

    except Exception as e:
        logger.error(f"\n❌ Tag migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_migration():
    """Verify that all tags were migrated correctly."""
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client["flask_db"]
    db = SessionLocal()

    try:
        # Get unique tags from MongoDB
        mongo_tags = extract_unique_tags_from_mongodb()

        # Get tags from PostgreSQL
        pg_tags = db.query(Tag).all()

        logger.info(f"\n📊 Verification:")
        logger.info(f"   MongoDB unique tags: {len(mongo_tags)}")
        logger.info(f"   PostgreSQL tags: {len(pg_tags)}")

        # Check for missing tags
        pg_tag_names = {tag.name for tag in pg_tags}
        missing = mongo_tags - pg_tag_names

        if missing:
            logger.warning(f"   ⚠️  Missing tags: {missing}")
            return False

        logger.info(f"   ✓ All tags present")

        # Show all tags
        logger.info(f"\n   Tags in PostgreSQL:")
        for tag in sorted(pg_tags, key=lambda x: x.name):
            logger.info(f"     • {tag.name} ({tag.id})")

        return True

    finally:
        db.close()
        mongo_client.close()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Phase 2: Migrate Tags")
    logger.info("=" * 60)

    # Run migration
    tag_map = migrate_tags()

    # Verify
    success = verify_migration()

    if success:
        logger.info(f"\n✅ Phase 2 (Tags) completed successfully!\n")
        sys.exit(0)
    else:
        logger.error(f"\n❌ Phase 2 (Tags) verification failed!\n")
        sys.exit(1)
