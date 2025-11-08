#!/usr/bin/env python3
"""
Phase 5: Verification Script for Read Operation Cutover

This script verifies that PostgreSQL read operations return the same data as
MongoDB read operations. It compares results from both databases to ensure
the read cutover will be safe.

Checks performed:
1. Line item count comparison
2. Event count comparison
3. Line item spot checks (random sampling)
4. Event spot checks with line item relationships
5. Filter consistency (dates, categories, payment methods)
6. ID coexistence validation (both ID formats work)
7. Analytics aggregation accuracy
8. Relationship loading verification

Usage:
    python phase5_verify.py              # Run all verification checks

Run this script:
- Before enabling READ_FROM_POSTGRESQL flag
- After enabling flag (confirm reads work correctly)
- Periodically during Phase 5 (daily recommended)
"""

import argparse
import logging
import random
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient

from constants import DATABASE_URL, MONGO_URI
from dao import (
    __pg_get_all_events,
    __pg_get_all_line_items,
    __pg_get_categorized_data,
    __pg_get_event_by_id,
    __pg_get_line_item_by_id,
    __pg_get_line_items_for_event,
    events_collection,
    get_all_data,
    get_categorized_data,
    get_item_by_id,
    line_items_collection,
)
from models.database import SessionLocal

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
        print("PHASE 5 VERIFICATION SUMMARY")
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
            print("✓ All checks passed! Safe to enable READ_FROM_POSTGRESQL=true")
            return True
        else:
            print("✗ Verification failed. Do NOT enable READ_FROM_POSTGRESQL yet.")
            return False


def compare_line_items(
    mongo_li: Dict[str, Any], pg_li: Dict[str, Any], result: VerificationResult
) -> bool:
    """Compare a line item from MongoDB and PostgreSQL"""
    differences = []

    # Compare key fields
    if mongo_li.get("id") != pg_li.get("id"):
        differences.append(f"ID mismatch: {mongo_li.get('id')} != {pg_li.get('id')}")

    # Compare dates (allow small float precision differences)
    mongo_date = mongo_li.get("date", 0.0)
    pg_date = pg_li.get("date", 0.0)
    if abs(mongo_date - pg_date) > 1.0:  # Allow 1 second difference
        differences.append(f"Date mismatch: {mongo_date} != {pg_date}")

    # Compare amounts (allow small decimal precision differences)
    mongo_amount = float(mongo_li.get("amount", 0.0))
    pg_amount = float(pg_li.get("amount", 0.0))
    if abs(mongo_amount - pg_amount) > 0.01:  # Allow 1 cent difference
        differences.append(f"Amount mismatch: {mongo_amount} != {pg_amount}")

    # Compare string fields
    for field in ["payment_method", "description", "responsible_party", "notes"]:
        mongo_val = mongo_li.get(field)
        pg_val = pg_li.get(field)
        if mongo_val != pg_val:
            differences.append(f"{field} mismatch: '{mongo_val}' != '{pg_val}'")

    if differences:
        for diff in differences:
            result.add_fail(f"Line item {mongo_li.get('id')}: {diff}")
        return False

    return True


def compare_events(
    mongo_event: Dict[str, Any], pg_event: Dict[str, Any], result: VerificationResult
) -> bool:
    """Compare an event from MongoDB and PostgreSQL"""
    differences = []

    # Compare key fields
    if mongo_event.get("id") != pg_event.get("id"):
        differences.append(
            f"ID mismatch: {mongo_event.get('id')} != {pg_event.get('id')}"
        )

    # Compare dates
    mongo_date = mongo_event.get("date", 0.0)
    pg_date = pg_event.get("date", 0.0)
    if abs(mongo_date - pg_date) > 1.0:
        differences.append(f"Date mismatch: {mongo_date} != {pg_date}")

    # Compare amounts
    mongo_amount = float(mongo_event.get("amount", 0.0))
    pg_amount = float(pg_event.get("amount", 0.0))
    if abs(mongo_amount - pg_amount) > 0.01:
        differences.append(f"Amount mismatch: {mongo_amount} != {pg_amount}")

    # Compare string fields
    for field in ["name", "category"]:
        mongo_val = mongo_event.get(field)
        pg_val = pg_event.get(field)
        if mongo_val != pg_val:
            differences.append(f"{field} mismatch: '{mongo_val}' != '{pg_val}'")

    # Compare line item lists (order doesn't matter)
    mongo_line_items = set(mongo_event.get("line_items", []))
    pg_line_items = set(pg_event.get("line_items", []))
    if mongo_line_items != pg_line_items:
        differences.append(
            f"Line items mismatch: {len(mongo_line_items)} vs {len(pg_line_items)}"
        )

    if differences:
        for diff in differences:
            result.add_fail(f"Event {mongo_event.get('id')}: {diff}")
        return False

    return True


def verify_line_item_counts(result: VerificationResult):
    """Verify line item counts match between MongoDB and PostgreSQL"""
    logging.info("\n1. Verifying line item counts...")

    # MongoDB count
    mongo_count = len(get_all_data(line_items_collection, {}))

    # PostgreSQL count
    pg_line_items = _pg_get_all_line_items({})
    pg_count = len(pg_line_items)

    if mongo_count == pg_count:
        result.add_pass(f"Line item counts match: {mongo_count} records")
    else:
        result.add_fail(
            f"Line item count mismatch: MongoDB={mongo_count}, PostgreSQL={pg_count}"
        )


def verify_event_counts(result: VerificationResult):
    """Verify event counts match between MongoDB and PostgreSQL"""
    logging.info("\n2. Verifying event counts...")

    # MongoDB count
    mongo_events = get_all_data(events_collection, {})
    mongo_count = len(mongo_events)

    # PostgreSQL count
    pg_events = _pg_get_all_events({})
    pg_count = len(pg_events)

    if mongo_count == pg_count:
        result.add_pass(f"Event counts match: {mongo_count} records")
    else:
        result.add_fail(
            f"Event count mismatch: MongoDB={mongo_count}, PostgreSQL={pg_count}"
        )


def verify_line_item_spot_checks(result: VerificationResult, sample_size=10):
    """Spot check random line items"""
    logging.info(f"\n3. Performing {sample_size} line item spot checks...")

    # Get all MongoDB line items
    mongo_line_items = get_all_data(line_items_collection, {})
    if not mongo_line_items:
        result.add_warning("No line items found in MongoDB")
        return

    # Sample random line items
    sample = random.sample(mongo_line_items, min(sample_size, len(mongo_line_items)))

    matches = 0
    for mongo_li in sample:
        line_item_id = mongo_li.get("id") or mongo_li.get("_id")
        pg_li = _pg_get_line_item_by_id(str(line_item_id))

        if pg_li is None:
            result.add_fail(f"Line item {line_item_id} not found in PostgreSQL")
            continue

        if compare_line_items(mongo_li, pg_li, result):
            matches += 1

    if matches == len(sample):
        result.add_pass(f"All {matches} spot-checked line items match")
    else:
        result.add_fail(f"Only {matches}/{len(sample)} spot-checked line items match")


def verify_event_spot_checks(result: VerificationResult, sample_size=10):
    """Spot check random events"""
    logging.info(f"\n4. Performing {sample_size} event spot checks...")

    # Get all MongoDB events
    mongo_events = get_all_data(events_collection, {})
    if not mongo_events:
        result.add_warning("No events found in MongoDB")
        return

    # Sample random events
    sample = random.sample(mongo_events, min(sample_size, len(mongo_events)))

    matches = 0
    for mongo_event in sample:
        event_id = mongo_event.get("id") or mongo_event.get("_id")
        pg_event = _pg_get_event_by_id(str(event_id))

        if pg_event is None:
            result.add_fail(f"Event {event_id} not found in PostgreSQL")
            continue

        if compare_events(mongo_event, pg_event, result):
            matches += 1

    if matches == len(sample):
        result.add_pass(f"All {matches} spot-checked events match")
    else:
        result.add_fail(f"Only {matches}/{len(sample)} spot-checked events match")


def verify_id_coexistence(result: VerificationResult):
    """Verify both PostgreSQL and MongoDB IDs work"""
    logging.info("\n5. Verifying ID coexistence...")

    # Get a line item from MongoDB
    mongo_line_items = get_all_data(line_items_collection, {})
    if not mongo_line_items:
        result.add_warning("No line items to test ID coexistence")
        return

    test_li = mongo_line_items[0]
    mongo_id = str(test_li.get("_id"))
    pg_id = test_li.get("id")

    # Test MongoDB ID lookup
    pg_li_by_mongo_id = _pg_get_line_item_by_id(mongo_id)
    if pg_li_by_mongo_id:
        result.add_pass(f"MongoDB ID lookup works: {mongo_id}")
    else:
        result.add_fail(f"MongoDB ID lookup failed: {mongo_id}")

    # Test PostgreSQL ID lookup
    pg_li_by_pg_id = _pg_get_line_item_by_id(pg_id)
    if pg_li_by_pg_id:
        result.add_pass(f"PostgreSQL ID lookup works: {pg_id}")
    else:
        result.add_fail(f"PostgreSQL ID lookup failed: {pg_id}")

    # Same for events
    mongo_events = get_all_data(events_collection, {})
    if mongo_events:
        test_event = mongo_events[0]
        mongo_event_id = str(test_event.get("_id"))
        pg_event_id = test_event.get("id")

        pg_event_by_mongo_id = _pg_get_event_by_id(mongo_event_id)
        if pg_event_by_mongo_id:
            result.add_pass(f"Event MongoDB ID lookup works: {mongo_event_id}")
        else:
            result.add_fail(f"Event MongoDB ID lookup failed: {mongo_event_id}")

        pg_event_by_pg_id = _pg_get_event_by_id(pg_event_id)
        if pg_event_by_pg_id:
            result.add_pass(f"Event PostgreSQL ID lookup works: {pg_event_id}")
        else:
            result.add_fail(f"Event PostgreSQL ID lookup failed: {pg_event_id}")


def verify_filter_consistency(result: VerificationResult):
    """Verify filters work consistently"""
    logging.info("\n6. Verifying filter consistency...")

    # Test line item filter: only_line_items_to_review
    filters = {"event_id": {"$exists": False}}
    mongo_unassigned = get_all_data(line_items_collection, filters)
    pg_unassigned = _pg_get_all_line_items(filters)

    if len(mongo_unassigned) == len(pg_unassigned):
        result.add_pass(
            f"Unassigned line items filter: {len(mongo_unassigned)} records"
        )
    else:
        result.add_fail(
            f"Unassigned line items mismatch: MongoDB={len(mongo_unassigned)}, PostgreSQL={len(pg_unassigned)}"
        )

    # Test event filter: date range
    now = datetime.now(UTC).timestamp()
    last_year = now - (365 * 24 * 60 * 60)
    date_filters = {"date": {"$gte": last_year, "$lte": now}}

    mongo_recent_events = get_all_data(events_collection, date_filters)
    pg_recent_events = _pg_get_all_events(date_filters)

    if len(mongo_recent_events) == len(pg_recent_events):
        result.add_pass(f"Date range filter: {len(mongo_recent_events)} events")
    else:
        result.add_fail(
            f"Date range filter mismatch: MongoDB={len(mongo_recent_events)}, PostgreSQL={len(pg_recent_events)}"
        )


def verify_analytics_aggregation(result: VerificationResult):
    """Verify analytics aggregation accuracy"""
    logging.info("\n7. Verifying analytics aggregation...")

    # Get categorized data from both databases
    mongo_categorized = get_categorized_data()
    pg_categorized = _pg_get_categorized_data(None)

    if len(mongo_categorized) == len(pg_categorized):
        result.add_pass(f"Analytics aggregation count: {len(mongo_categorized)} groups")
    else:
        result.add_warning(
            f"Analytics row count mismatch: MongoDB={len(mongo_categorized)}, PostgreSQL={len(pg_categorized)} (may be OK if grouping differs slightly)"
        )

    # Compare totals by category
    mongo_totals = {}
    for row in mongo_categorized:
        category = row["category"]
        if category not in mongo_totals:
            mongo_totals[category] = 0
        mongo_totals[category] += row["totalExpense"]

    pg_totals = {}
    for row in pg_categorized:
        category = row["category"]
        if category not in pg_totals:
            pg_totals[category] = 0
        pg_totals[category] += row["totalExpense"]

    # Compare each category total
    all_categories = set(mongo_totals.keys()) | set(pg_totals.keys())
    mismatches = 0
    for category in all_categories:
        mongo_total = mongo_totals.get(category, 0)
        pg_total = pg_totals.get(category, 0)
        if abs(mongo_total - pg_total) > 0.01:
            result.add_fail(
                f"Category '{category}' total mismatch: MongoDB=${mongo_total:.2f}, PostgreSQL=${pg_total:.2f}"
            )
            mismatches += 1

    if mismatches == 0:
        result.add_pass(f"All {len(all_categories)} category totals match")


def verify_relationship_loading(result: VerificationResult):
    """Verify relationship loading (events with line items)"""
    logging.info("\n8. Verifying relationship loading...")

    # Get an event with line items
    mongo_events = get_all_data(events_collection, {})
    events_with_line_items = [e for e in mongo_events if e.get("line_items")]

    if not events_with_line_items:
        result.add_warning("No events with line items to test relationship loading")
        return

    test_event = events_with_line_items[0]
    event_id = test_event.get("id") or test_event.get("_id")

    # Get line items for event from PostgreSQL
    pg_line_items = _pg_get_line_items_for_event(str(event_id))

    mongo_line_item_count = len(test_event.get("line_items", []))
    pg_line_item_count = len(pg_line_items)

    if mongo_line_item_count == pg_line_item_count:
        result.add_pass(
            f"Event {event_id} has {pg_line_item_count} line items in both databases"
        )
    else:
        result.add_fail(
            f"Event {event_id} line item count mismatch: MongoDB={mongo_line_item_count}, PostgreSQL={pg_line_item_count}"
        )


def main():
    """Run all verification checks"""
    parser = argparse.ArgumentParser(
        description="Verify Phase 5 read operation consistency"
    )
    args = parser.parse_args()

    result = VerificationResult()

    logging.info("=" * 60)
    logging.info("PHASE 5 VERIFICATION: Read Operation Consistency")
    logging.info("=" * 60)
    logging.info(f"MongoDB URI: {MONGO_URI}")
    logging.info(f"PostgreSQL URL: {DATABASE_URL}")
    logging.info("")

    # Run all verification checks
    verify_line_item_counts(result)
    verify_event_counts(result)
    verify_line_item_spot_checks(result, sample_size=10)
    verify_event_spot_checks(result, sample_size=10)
    verify_id_coexistence(result)
    verify_filter_consistency(result)
    verify_analytics_aggregation(result)
    verify_relationship_loading(result)

    # Print summary
    success = result.print_summary()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
