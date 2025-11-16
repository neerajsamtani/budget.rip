#!/usr/bin/env python3
"""
Phase 4: Verification Script for Events and Tags

This script verifies data consistency between MongoDB and PostgreSQL after
Phase 4 migration. It performs:
1. Count verification for tags, events, and junction tables
2. Spot checks or full field-by-field verification
3. Foreign key integrity checks
4. Event-line item relationship verification
5. Event-tag relationship verification
6. Detailed error reporting

Usage:
    python phase4_verify.py              # Default: spot check mode
    python phase4_verify.py --thorough   # Full verification (checks every record)

Run this script:
- After initial migration (phase4_migrate_events.py)
- Periodically during dual-write period
- Before switching reads to PostgreSQL (Phase 5)
"""

import argparse
import logging
import random
import sys
from pathlib import Path
from typing import List, Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from sqlalchemy import func

from constants import MONGO_URI
from dao import events_collection
from models.database import SessionLocal
from models.sql_models import Category, Event, EventLineItem, EventTag, LineItem, Tag

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class VerificationResult:
    """Track verification results"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors: List[str] = []

    def add_pass(self, message: str):
        """Add a passing check"""
        self.passed += 1
        logging.info(f"  ✓ {message}")

    def add_fail(self, message: str):
        """Add a failing check"""
        self.failed += 1
        self.errors.append(message)
        logging.error(f"  ✗ {message}")

    def add_warning(self, message: str):
        """Add a warning"""
        self.warnings += 1
        logging.warning(f"  ⚠ {message}")

    def print_summary(self):
        """Print verification summary"""
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"Passed:   {self.passed}")
        print(f"Failed:   {self.failed}")
        print(f"Warnings: {self.warnings}")

        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")

        print("=" * 60)

        if self.failed == 0:
            print("✓ All checks passed!")
            return True
        else:
            print("✗ Verification failed")
            return False


def extract_unique_tags(mongo_db) -> Set[str]:
    """Extract all unique tag strings from MongoDB events"""
    events = mongo_db[events_collection]
    events_with_tags = events.find({"tags": {"$exists": True, "$ne": []}})

    unique_tags = set()
    for event in events_with_tags:
        tags = event.get("tags", [])
        if isinstance(tags, list):
            unique_tags.update(tags)

    return unique_tags


def verify_tag_counts(mongo_db, db_session, result: VerificationResult):
    """Verify tag counts match between MongoDB and PostgreSQL"""
    logging.info("\n[1] Verifying Tag Counts")

    unique_mongo_tags = extract_unique_tags(mongo_db)
    pg_tag_count = db_session.query(Tag).count()

    if len(unique_mongo_tags) == pg_tag_count:
        result.add_pass(f"Tags: {len(unique_mongo_tags)} = {pg_tag_count}")
    else:
        result.add_fail(
            f"Tags: {len(unique_mongo_tags)} MongoDB unique ≠ {pg_tag_count} PostgreSQL"
        )

    # Verify all MongoDB tags exist in PostgreSQL
    pg_tag_names = {tag.name for tag in db_session.query(Tag).all()}
    missing_tags = unique_mongo_tags - pg_tag_names

    if not missing_tags:
        result.add_pass("All MongoDB tags exist in PostgreSQL")
    else:
        result.add_fail(f"Missing tags in PostgreSQL: {missing_tags}")


def verify_event_counts(mongo_db, db_session, result: VerificationResult):
    """Verify event counts match"""
    logging.info("\n[2] Verifying Event Counts")

    mongo_count = mongo_db[events_collection].count_documents({})
    pg_count = db_session.query(Event).count()

    if mongo_count == pg_count:
        result.add_pass(f"Events: {mongo_count} = {pg_count}")
    else:
        result.add_fail(f"Events: {mongo_count} MongoDB ≠ {pg_count} PostgreSQL")


def verify_event_line_item_counts(mongo_db, db_session, result: VerificationResult):
    """Verify EventLineItem junction table counts"""
    logging.info("\n[3] Verifying EventLineItem Junction Counts")

    # Count total line_items across all MongoDB events
    events = mongo_db[events_collection]
    total_line_items = 0
    for event in events.find():
        line_items = event.get("line_items", [])
        total_line_items += len(line_items)

    pg_junction_count = db_session.query(EventLineItem).count()

    if total_line_items == pg_junction_count:
        result.add_pass(
            f"EventLineItem junctions: {total_line_items} = {pg_junction_count}"
        )
    else:
        result.add_fail(
            f"EventLineItem junctions: {total_line_items} MongoDB ≠ {pg_junction_count} PostgreSQL"
        )


def verify_event_tag_counts(mongo_db, db_session, result: VerificationResult):
    """Verify EventTag junction table counts"""
    logging.info("\n[4] Verifying EventTag Junction Counts")

    # Count total tags across all MongoDB events
    events = mongo_db[events_collection]
    total_tags = 0
    for event in events.find():
        tags = event.get("tags", [])
        if isinstance(tags, list):
            total_tags += len(tags)

    pg_junction_count = db_session.query(EventTag).count()

    if total_tags == pg_junction_count:
        result.add_pass(f"EventTag junctions: {total_tags} = {pg_junction_count}")
    else:
        result.add_fail(
            f"EventTag junctions: {total_tags} MongoDB ≠ {pg_junction_count} PostgreSQL"
        )


def verify_event_spot_checks(
    mongo_db, db_session, result: VerificationResult, sample_size: int = 50
):
    """Perform spot checks on random events"""
    logging.info(f"\n[5] Verifying Event Spot Checks (sample size: {sample_size})")

    events = mongo_db[events_collection]
    all_mongo_ids = [str(event["_id"]) for event in events.find({}, {"_id": 1})]

    if len(all_mongo_ids) == 0:
        result.add_warning("No MongoDB events to verify")
        return

    sample_ids = random.sample(all_mongo_ids, min(sample_size, len(all_mongo_ids)))

    mismatches = 0
    for mongo_id in sample_ids:
        mongo_event = events.find_one({"_id": mongo_id})
        pg_event = (
            db_session.query(Event).filter(Event.mongo_id == str(mongo_id)).first()
        )

        if not pg_event:
            result.add_fail(f"Event {mongo_id} not found in PostgreSQL")
            mismatches += 1
            continue

        # Verify description field (MongoDB uses 'name', PostgreSQL uses 'description')
        mongo_description = mongo_event.get("name", mongo_event.get("description", ""))
        if mongo_description != pg_event.description:
            result.add_fail(
                f"Event {mongo_id}: description mismatch: '{mongo_description}' ≠ '{pg_event.description}'"
            )
            mismatches += 1

        # Verify category
        mongo_category = mongo_event.get("category")
        if (
            mongo_category
            and pg_event.category
            and mongo_category != pg_event.category.name
        ):
            result.add_fail(
                f"Event {mongo_id}: category mismatch: '{mongo_category}' ≠ '{pg_event.category.name}'"
            )
            mismatches += 1

        # Verify is_duplicate
        mongo_is_dup = mongo_event.get("is_duplicate_transaction", False)
        if bool(mongo_is_dup) != pg_event.is_duplicate:
            result.add_fail(
                f"Event {mongo_id}: is_duplicate mismatch: {mongo_is_dup} ≠ {pg_event.is_duplicate}"
            )
            mismatches += 1

        # Verify line items count
        mongo_line_items = mongo_event.get("line_items", [])
        pg_line_items_count = (
            db_session.query(EventLineItem)
            .filter(EventLineItem.event_id == pg_event.id)
            .count()
        )

        if len(mongo_line_items) != pg_line_items_count:
            result.add_fail(
                f"Event {mongo_id}: line items count mismatch: {len(mongo_line_items)} ≠ {pg_line_items_count}"
            )
            mismatches += 1

        # Verify tags count
        mongo_tags = mongo_event.get("tags", [])
        pg_tags_count = (
            db_session.query(EventTag).filter(EventTag.event_id == pg_event.id).count()
        )

        if len(mongo_tags) != pg_tags_count:
            result.add_fail(
                f"Event {mongo_id}: tags count mismatch: {len(mongo_tags)} ≠ {pg_tags_count}"
            )
            mismatches += 1

    if mismatches == 0:
        result.add_pass(f"All {len(sample_ids)} spot checked events match")
    else:
        result.add_fail(f"{mismatches} mismatches found in spot check")


def verify_event_thorough(mongo_db, db_session, result: VerificationResult):
    """Perform thorough verification of ALL events"""
    logging.info("\n[5] Verifying Events (THOROUGH - checking every record)")

    events = mongo_db[events_collection]
    total_events = events.count_documents({})
    logging.info(f"Checking {total_events} events...")

    mismatches = 0
    checked = 0

    for mongo_event in events.find():
        checked += 1
        mongo_id = str(mongo_event.get("_id", mongo_event.get("id")))

        pg_event = db_session.query(Event).filter(Event.mongo_id == mongo_id).first()

        if not pg_event:
            result.add_fail(f"Event {mongo_id} not found in PostgreSQL")
            mismatches += 1
            continue

        # Verify all fields (MongoDB uses 'name', PostgreSQL uses 'description')
        mongo_description = mongo_event.get("name", mongo_event.get("description", ""))
        if mongo_description != pg_event.description:
            result.add_fail(f"Event {mongo_id}: description mismatch")
            mismatches += 1

        mongo_category = mongo_event.get("category")
        if (
            mongo_category
            and pg_event.category
            and mongo_category != pg_event.category.name
        ):
            result.add_fail(f"Event {mongo_id}: category mismatch")
            mismatches += 1

        mongo_is_dup = mongo_event.get("is_duplicate_transaction", False)
        if bool(mongo_is_dup) != pg_event.is_duplicate:
            result.add_fail(f"Event {mongo_id}: is_duplicate mismatch")
            mismatches += 1

        # Verify line items
        mongo_line_items = mongo_event.get("line_items", [])
        pg_line_items_count = (
            db_session.query(EventLineItem)
            .filter(EventLineItem.event_id == pg_event.id)
            .count()
        )

        if len(mongo_line_items) != pg_line_items_count:
            result.add_fail(f"Event {mongo_id}: line items count mismatch")
            mismatches += 1

        # Verify tags
        mongo_tags = mongo_event.get("tags", [])
        pg_tags_count = (
            db_session.query(EventTag).filter(EventTag.event_id == pg_event.id).count()
        )

        if len(mongo_tags) != pg_tags_count:
            result.add_fail(f"Event {mongo_id}: tags count mismatch")
            mismatches += 1

        # Progress reporting
        if checked % 500 == 0:
            logging.info(f"Progress: {checked}/{total_events} events checked")

    if mismatches == 0:
        result.add_pass(f"All {checked} events match perfectly")
    else:
        result.add_fail(f"{mismatches} total mismatches found in thorough check")


def verify_foreign_key_integrity(db_session, result: VerificationResult):
    """Verify foreign key integrity in PostgreSQL"""
    logging.info("\n[6] Verifying Foreign Key Integrity")

    # Check events have valid categories
    events_without_category = (
        db_session.query(Event)
        .outerjoin(Category)
        .filter(Category.id.is_(None))
        .count()
    )

    if events_without_category == 0:
        result.add_pass("All events have valid categories")
    else:
        result.add_fail(f"{events_without_category} events have invalid category_id")

    # Check EventLineItem junctions have valid events and line items
    invalid_event_junctions = (
        db_session.query(EventLineItem)
        .outerjoin(Event, EventLineItem.event_id == Event.id)
        .filter(Event.id.is_(None))
        .count()
    )

    if invalid_event_junctions == 0:
        result.add_pass("All EventLineItem junctions have valid event_id")
    else:
        result.add_fail(
            f"{invalid_event_junctions} EventLineItem junctions have invalid event_id"
        )

    invalid_line_item_junctions = (
        db_session.query(EventLineItem)
        .outerjoin(LineItem, EventLineItem.line_item_id == LineItem.id)
        .filter(LineItem.id.is_(None))
        .count()
    )

    if invalid_line_item_junctions == 0:
        result.add_pass("All EventLineItem junctions have valid line_item_id")
    else:
        result.add_fail(
            f"{invalid_line_item_junctions} EventLineItem junctions have invalid line_item_id"
        )

    # Check EventTag junctions have valid events and tags
    invalid_event_tag_junctions = (
        db_session.query(EventTag)
        .outerjoin(Event, EventTag.event_id == Event.id)
        .filter(Event.id.is_(None))
        .count()
    )

    if invalid_event_tag_junctions == 0:
        result.add_pass("All EventTag junctions have valid event_id")
    else:
        result.add_fail(
            f"{invalid_event_tag_junctions} EventTag junctions have invalid event_id"
        )

    invalid_tag_junctions = (
        db_session.query(EventTag)
        .outerjoin(Tag, EventTag.tag_id == Tag.id)
        .filter(Tag.id.is_(None))
        .count()
    )

    if invalid_tag_junctions == 0:
        result.add_pass("All EventTag junctions have valid tag_id")
    else:
        result.add_fail(
            f"{invalid_tag_junctions} EventTag junctions have invalid tag_id"
        )


def verify_mongo_id_uniqueness(db_session, result: VerificationResult):
    """Verify mongo_id uniqueness in PostgreSQL"""
    logging.info("\n[7] Verifying mongo_id Uniqueness")

    # Check for duplicate mongo_ids
    duplicates = (
        db_session.query(Event.mongo_id, func.count(Event.mongo_id))
        .group_by(Event.mongo_id)
        .having(func.count(Event.mongo_id) > 1)
        .all()
    )

    if len(duplicates) == 0:
        result.add_pass("All mongo_ids are unique")
    else:
        result.add_fail(f"{len(duplicates)} duplicate mongo_ids found")
        for mongo_id, count in duplicates[:5]:  # Show first 5
            result.add_fail(f"  mongo_id {mongo_id} appears {count} times")


def main():
    """Main verification function"""
    parser = argparse.ArgumentParser(description="Phase 4 Verification Script")
    parser.add_argument(
        "--thorough",
        action="store_true",
        help="Perform thorough verification (check every record)",
    )
    args = parser.parse_args()

    logging.info("=" * 60)
    logging.info("Phase 4: Event and Tag Verification")
    logging.info("Mode: " + ("THOROUGH" if args.thorough else "SPOT CHECK"))
    logging.info("=" * 60)

    # Connect to databases
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client.get_default_database()
    db_session = SessionLocal()

    result = VerificationResult()

    try:
        # Run verification checks
        verify_tag_counts(mongo_db, db_session, result)
        verify_event_counts(mongo_db, db_session, result)
        verify_event_line_item_counts(mongo_db, db_session, result)
        verify_event_tag_counts(mongo_db, db_session, result)

        if args.thorough:
            verify_event_thorough(mongo_db, db_session, result)
        else:
            verify_event_spot_checks(mongo_db, db_session, result, sample_size=50)

        verify_foreign_key_integrity(db_session, result)
        verify_mongo_id_uniqueness(db_session, result)

        # Print summary
        success = result.print_summary()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except Exception as e:
        logging.error(f"Verification failed with error: {e}")
        raise

    finally:
        db_session.close()
        mongo_client.close()


if __name__ == "__main__":
    main()
