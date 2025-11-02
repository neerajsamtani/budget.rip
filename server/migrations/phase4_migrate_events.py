#!/usr/bin/env python3
"""
Phase 4: Migrate Events and Tags from MongoDB to PostgreSQL

This script migrates events and tags from MongoDB to PostgreSQL:
1. Extracts and migrates unique tags from MongoDB events
2. Migrates events with relationships to line items, categories, and tags
3. Creates EventLineItem and EventTag junction table records
4. Stores original MongoDB _id in mongo_id column for ID coexistence

Prerequisites:
- Phase 2 complete (categories migrated)
- Phase 3 complete (line items migrated with mongo_id)
"""

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient

from constants import DATABASE_URL, MONGO_URI
from dao import events_collection
from models.database import SessionLocal
from models.sql_models import Category, Event, EventLineItem, EventTag, LineItem, Tag
from utils.id_generator import generate_id

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def extract_unique_tags(mongo_client) -> Set[str]:
    """
    Extract all unique tag strings from MongoDB events.

    Args:
        mongo_client: MongoDB client

    Returns:
        Set of unique tag strings
    """
    logging.info("Extracting unique tags from MongoDB events...")

    db = mongo_client.get_default_database()
    events = db[events_collection]

    # Find all events with tags
    events_with_tags = events.find({"tags": {"$exists": True, "$ne": []}})

    unique_tags = set()
    for event in events_with_tags:
        tags = event.get("tags", [])
        if isinstance(tags, list):
            unique_tags.update(tags)

    logging.info(f"Found {len(unique_tags)} unique tags")
    logging.info(f"Unique tags: {unique_tags}")
    return unique_tags


def migrate_tags(db_session, unique_tags: Set[str]) -> Dict[str, str]:
    """
    Migrate tags to PostgreSQL.

    Args:
        db_session: SQLAlchemy session
        unique_tags: Set of unique tag strings

    Returns:
        Dictionary mapping tag name -> tag_id
    """
    logging.info(f"Migrating {len(unique_tags)} tags to PostgreSQL...")

    tag_map = {}
    created_count = 0
    skipped_count = 0

    for tag_name in sorted(unique_tags):
        # Check if tag already exists
        existing_tag = db_session.query(Tag).filter(Tag.name == tag_name).first()

        if existing_tag:
            tag_map[tag_name] = existing_tag.id
            skipped_count += 1
            continue

        # Create new tag
        tag_id = generate_id("tag")
        tag = Tag(
            id=tag_id,
            name=tag_name,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        db_session.add(tag)
        tag_map[tag_name] = tag_id
        created_count += 1

    db_session.commit()

    logging.info(
        f"Tags migration complete: {created_count} created, {skipped_count} already existed"
    )
    return tag_map


def get_category_map(db_session) -> Dict[str, str]:
    """
    Get mapping of category name -> id

    Args:
        db_session: SQLAlchemy session

    Returns:
        Dictionary mapping category name to ID
    """
    categories = db_session.query(Category).all()
    return {cat.name: cat.id for cat in categories}


def get_line_item_map(db_session) -> Dict[str, str]:
    """
    Get mapping of mongo_id -> line_item_id

    Args:
        db_session: SQLAlchemy session

    Returns:
        Dictionary mapping MongoDB _id to PostgreSQL line item ID
    """
    line_items = db_session.query(LineItem).filter(LineItem.mongo_id.isnot(None)).all()
    return {li.mongo_id: li.id for li in line_items}


def migrate_events(
    mongo_client,
    db_session,
    category_map: Dict[str, str],
    line_item_map: Dict[str, str],
    tag_map: Dict[str, str],
):
    """
    Migrate events from MongoDB to PostgreSQL.

    Args:
        mongo_client: MongoDB client
        db_session: SQLAlchemy session
        category_map: Mapping of category name to ID
        line_item_map: Mapping of MongoDB line item _id to PostgreSQL ID
        tag_map: Mapping of tag name to ID
    """
    logging.info("Starting event migration...")

    db = mongo_client.get_default_database()
    events = db[events_collection]

    total_events = events.count_documents({})
    logging.info(f"Found {total_events} events to migrate")

    migrated_count = 0
    skipped_count = 0
    error_count = 0

    for event_data in events.find():
        try:
            mongo_id = str(event_data.get("_id", event_data.get("id")))

            # Check if event already migrated
            existing_event = (
                db_session.query(Event).filter(Event.mongo_id == mongo_id).first()
            )
            if existing_event:
                skipped_count += 1
                if (migrated_count + skipped_count) % 100 == 0:
                    logging.info(
                        f"Progress: {migrated_count + skipped_count}/{total_events} events processed"
                    )
                continue

            # Look up category_id
            category_name = event_data.get("category")
            if not category_name:
                raise ValueError(f"Event {mongo_id} missing category")

            if category_name not in category_map:
                raise ValueError(
                    f"Event {mongo_id} has invalid category '{category_name}'"
                )

            category_id = category_map[category_name]

            # Generate new PostgreSQL ID with event_ prefix
            event_id = generate_id("event")

            # Parse date
            event_date = event_data.get("date")
            if isinstance(event_date, (int, float)):
                event_date = datetime.fromtimestamp(event_date, UTC)
            elif not isinstance(event_date, datetime):
                raise ValueError(f"Event {mongo_id} has invalid date: {event_date}")

            is_duplicate = bool(event_data.get("is_duplicate_transaction", False))

            # Create Event record
            event = Event(
                id=event_id,
                mongo_id=mongo_id,
                date=event_date,
                description=event_data.get("description", ""),
                category_id=category_id,
                is_duplicate=is_duplicate,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            db_session.add(event)

            # Create EventLineItem junctions
            line_item_ids = event_data.get("line_items", [])
            for li_mongo_id in line_item_ids:
                li_id_str = str(li_mongo_id)

                if li_id_str not in line_item_map:
                    raise ValueError(
                        f"Event {mongo_id} references missing line item {li_id_str}"
                    )

                line_item_id = line_item_map[li_id_str]

                event_line_item = EventLineItem(
                    id=generate_id("eli"),
                    event_id=event_id,
                    line_item_id=line_item_id,
                    created_at=datetime.now(UTC),
                )
                db_session.add(event_line_item)

            # Create EventTag junctions
            tags = event_data.get("tags", [])
            if isinstance(tags, list):
                for tag_name in tags:
                    if tag_name not in tag_map:
                        raise ValueError(
                            f"Event {mongo_id} references missing tag '{tag_name}'"
                        )

                    tag_id = tag_map[tag_name]

                    event_tag = EventTag(
                        id=generate_id("etag"),
                        event_id=event_id,
                        tag_id=tag_id,
                        created_at=datetime.now(UTC),
                    )
                    db_session.add(event_tag)
            elif tags is not None:
                raise ValueError(
                    f"Event {mongo_id} has invalid tags field type: {type(tags)}"
                )

            migrated_count += 1

            # Commit in batches
            if migrated_count % 100 == 0:
                db_session.commit()
                logging.info(
                    f"Progress: {migrated_count + skipped_count}/{total_events} events processed"
                )

        except Exception as e:
            logging.error(f"Error migrating event {mongo_id}: {e}")
            error_count += 1
            db_session.rollback()

    # Final commit
    db_session.commit()

    logging.info("\nEvent migration complete!")
    logging.info(f"  Migrated: {migrated_count}")
    logging.info(f"  Skipped (already existed): {skipped_count}")
    logging.info(f"  Errors: {error_count}")


def verify_migration(db_session, mongo_client):
    """
    Verify the migration by comparing counts.

    Args:
        db_session: SQLAlchemy session
        mongo_client: MongoDB client
    """
    logging.info("\n" + "=" * 60)
    logging.info("VERIFICATION")
    logging.info("=" * 60)

    db = mongo_client.get_default_database()

    # Count tags
    mongo_events = db[events_collection]
    unique_tags = extract_unique_tags(mongo_client)
    pg_tags = db_session.query(Tag).all()
    pg_tag_names = {tag.name for tag in pg_tags}
    pg_tags_count = len(pg_tags)

    logging.info("\nTags:")
    logging.info(f"  MongoDB unique tags: {len(unique_tags)}")
    logging.info(f"  PostgreSQL tags count: {pg_tags_count}")
    logging.info(f"  PostgreSQL tags: {pg_tag_names}")

    if len(unique_tags) == pg_tags_count:
        logging.info("  ✓ Tag counts match!")
    else:
        logging.warning("  ✗ Tag counts don't match!")

    # Count events
    mongo_event_count = mongo_events.count_documents({})
    pg_event_count = db_session.query(Event).count()

    logging.info("\nEvents:")
    logging.info(f"  MongoDB events: {mongo_event_count}")
    logging.info(f"  PostgreSQL events: {pg_event_count}")

    if mongo_event_count == pg_event_count:
        logging.info("  ✓ Event counts match!")
    else:
        logging.warning("  ✗ Event counts don't match!")

    # Count EventLineItem junctions
    pg_event_line_item_count = db_session.query(EventLineItem).count()
    logging.info(f"\nEventLineItem junctions: {pg_event_line_item_count}")

    # Count EventTag junctions
    pg_event_tag_count = db_session.query(EventTag).count()
    logging.info(f"EventTag junctions: {pg_event_tag_count}")

    logging.info("\n" + "=" * 60)


def main():
    """Main migration function"""
    logging.info("Starting Phase 4: Event and Tag Migration")
    logging.info(f"MongoDB URI: {MONGO_URI}")
    logging.info(f"PostgreSQL URL: {DATABASE_URL}")
    logging.info("")

    # Connect to databases
    mongo_client = MongoClient(MONGO_URI)
    db_session = SessionLocal()

    try:
        # Step 1: Extract and migrate tags
        unique_tags = extract_unique_tags(mongo_client)
        tag_map = migrate_tags(db_session, unique_tags)

        # Step 2: Build lookup maps
        category_map = get_category_map(db_session)
        line_item_map = get_line_item_map(db_session)

        logging.info("\nLookup maps built:")
        logging.info(f"  Categories: {len(category_map)}")
        logging.info(f"  Line items: {len(line_item_map)}")
        logging.info(f"  Tags: {len(tag_map)}")

        # Step 3: Migrate events
        migrate_events(mongo_client, db_session, category_map, line_item_map, tag_map)

        # Step 4: Verify migration
        verify_migration(db_session, mongo_client)

        logging.info("\n✓ Phase 4 migration complete!")
        logging.info("Run phase4_verify.py for detailed verification")

    except Exception as e:
        logging.error(f"Migration failed: {e}")
        db_session.rollback()
        raise

    finally:
        db_session.close()
        mongo_client.close()


if __name__ == "__main__":
    main()
