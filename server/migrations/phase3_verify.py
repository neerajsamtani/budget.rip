#!/usr/bin/env python3
"""
Phase 3: Verification Script for Transactions and Line Items

This script verifies data consistency between MongoDB and PostgreSQL after
Phase 3 migration. It performs:
1. Count verification for transactions and line items
2. Full field-by-field verification (or quick spot checks)
3. Bidirectional verification (no extra records)
4. Transaction date accuracy verification
5. Payment method mapping verification
6. Aggregate totals verification
7. Foreign key integrity checks
8. Detailed error reporting

Usage:
    python phase3_verify.py              # Default: thorough verification
    python phase3_verify.py --quick      # Quick verification (spot checks only)
    python phase3_verify.py --thorough   # Full verification (checks every record)

Run this script:
- After initial migration (phase3_migrate_*.py)
- Periodically during dual-write period (e.g., hourly cron job)
- Before switching reads to PostgreSQL (Phase 5)
"""

import argparse
import logging
import random
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from sqlalchemy import func

from constants import DATABASE_URL, MONGO_URI
from dao import line_items_collection
from helpers import iso_8601_to_posix
from models.database import SessionLocal
from models.sql_models import LineItem, PaymentMethod, Transaction

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


def verify_transaction_counts(mongo_db, db_session, result: VerificationResult):
    """Verify transaction counts match between MongoDB and PostgreSQL"""
    logging.info("\n[1] Verifying Transaction Counts")

    # Collection to source mapping
    collections = {
        "venmo_raw_data": "venmo",
        "splitwise_raw_data": "splitwise",
        "stripe_raw_transaction_data": "stripe",
        "cash_raw_data": "cash",
    }

    for collection_name, source in collections.items():
        mongo_count = mongo_db[collection_name].count_documents({})
        pg_count = db_session.query(Transaction).filter_by(source=source).count()

        if mongo_count == pg_count:
            result.add_pass(f"{collection_name}: {mongo_count} = {pg_count}")
        else:
            result.add_fail(
                f"{collection_name}: {mongo_count} MongoDB ≠ {pg_count} PostgreSQL"
            )

    # Total counts
    total_mongo = sum(mongo_db[coll].count_documents({}) for coll in collections.keys())
    total_pg = db_session.query(Transaction).count()

    if total_mongo == total_pg:
        result.add_pass(f"Total transactions: {total_mongo} = {total_pg}")
    else:
        result.add_fail(
            f"Total transactions: {total_mongo} MongoDB ≠ {total_pg} PostgreSQL"
        )


def verify_line_item_counts(mongo_db, db_session, result: VerificationResult):
    """Verify line item counts match"""
    logging.info("\n[2] Verifying Line Item Counts")

    mongo_count = mongo_db[line_items_collection].count_documents({})
    pg_count = db_session.query(LineItem).count()

    if mongo_count == pg_count:
        result.add_pass(f"Line items: {mongo_count} = {pg_count}")
    else:
        result.add_fail(f"Line items: {mongo_count} MongoDB ≠ {pg_count} PostgreSQL")


def verify_transaction_spot_checks(mongo_db, db_session, result: VerificationResult):
    """Spot check transaction data integrity (quick mode)"""
    logging.info("\n[3] Spot Checking Transactions (10 random samples)")

    collections = {
        "venmo_raw_data": "venmo",
        "splitwise_raw_data": "splitwise",
        "stripe_raw_transaction_data": "stripe",
        "cash_raw_data": "cash",
    }

    for collection_name, source in collections.items():
        # Get a few random documents
        mongo_docs = list(mongo_db[collection_name].find().limit(10))

        if not mongo_docs:
            result.add_warning(f"No documents in {collection_name}")
            continue

        # Sample up to 3 random docs
        sample_size = min(3, len(mongo_docs))
        samples = random.sample(mongo_docs, sample_size)

        for doc in samples:
            mongo_id = str(doc["_id"])

            # Find in PostgreSQL
            pg_txn = (
                db_session.query(Transaction)
                .filter_by(source=source, source_id=mongo_id)
                .first()
            )

            if not pg_txn:
                result.add_fail(
                    f"Transaction not found in PostgreSQL: {source}:{mongo_id}"
                )
                continue

            # Verify source_data contains original data
            if not pg_txn.source_data:
                result.add_fail(f"Missing source_data for {source}:{mongo_id}")
                continue

            result.add_pass(f"Transaction verified: {source}:{mongo_id[:8]}...")


def verify_all_transactions(mongo_db, db_session, result: VerificationResult):
    """Verify ALL transactions (thorough mode)"""
    logging.info("\n[3] Verifying ALL Transactions (Full Verification)")

    collections = {
        "venmo_raw_data": "venmo",
        "splitwise_raw_data": "splitwise",
        "stripe_raw_transaction_data": "stripe",
        "cash_raw_data": "cash",
    }

    # Build lookup dict for PostgreSQL transactions
    logging.info("  Building PostgreSQL transaction lookup index...")
    pg_txns_dict = {}
    for txn in db_session.query(Transaction).all():
        key = f"{txn.source}:{txn.source_id}"
        pg_txns_dict[key] = txn

    errors = []
    checked = 0
    last_log = 0

    for collection_name, source in collections.items():
        total = mongo_db[collection_name].count_documents({})
        if total == 0:
            result.add_warning(f"No documents in {collection_name}")
            continue

        logging.info(f"  Checking {total} {source} transactions...")

        for doc in mongo_db[collection_name].find():
            mongo_id = str(doc["_id"])
            key = f"{source}:{mongo_id}"
            pg_txn = pg_txns_dict.get(key)

            if not pg_txn:
                errors.append(f"Missing in PostgreSQL: {key}")
                continue

            # Verify source_data exists and is not empty
            if not pg_txn.source_data:
                errors.append(f"{key}: Missing source_data")

            # Verify transaction date matches
            if source == "stripe":
                expected = datetime.fromtimestamp(
                    float(doc.get("transacted_at", 0)), UTC
                )
            elif source == "venmo":
                expected = datetime.fromtimestamp(
                    float(doc.get("date_created", 0)), UTC
                )
            elif source == "splitwise":
                iso_date = doc.get("date", "")
                posix_timestamp = iso_8601_to_posix(iso_date)
                expected = datetime.fromtimestamp(posix_timestamp, UTC)
            elif source == "cash":
                expected = datetime.fromtimestamp(float(doc.get("date", 0)), UTC)
            else:
                continue

            if pg_txn.transaction_date != expected:
                errors.append(f"{key}: date mismatch")

            checked += 1
            if checked % 1000 == 0 and checked != last_log:
                logging.info(f"  Checked {checked} transactions...")
                last_log = checked

    if errors:
        for error in errors[:20]:
            result.add_fail(error)
        if len(errors) > 20:
            result.add_fail(f"... and {len(errors) - 20} more transaction errors")
    else:
        result.add_pass(f"All {checked} transactions verified")


def verify_line_item_spot_checks(mongo_db, db_session, result: VerificationResult):
    """Spot check line item data integrity (quick mode)"""
    logging.info("\n[4] Spot Checking Line Items (10 random samples)")

    # Get random line items from MongoDB
    mongo_items = list(mongo_db[line_items_collection].find().limit(50))

    if not mongo_items:
        result.add_warning("No line items in MongoDB")
        return

    # Sample up to 10
    sample_size = min(10, len(mongo_items))
    samples = random.sample(mongo_items, sample_size)

    for doc in samples:
        mongo_id = str(doc["_id"])

        # Find in PostgreSQL
        pg_item = db_session.query(LineItem).filter_by(mongo_id=mongo_id).first()

        if not pg_item:
            result.add_fail(f"Line item not found in PostgreSQL: {mongo_id}")
            continue

        # Verify fields match
        errors = []

        # Amount
        if abs(float(pg_item.amount) - float(doc["amount"])) > 0.01:
            errors.append(f"Amount mismatch: {doc['amount']} ≠ {pg_item.amount}")

        # Description
        if pg_item.description != doc.get("description", ""):
            errors.append(
                f"Description mismatch: '{doc.get('description')}' ≠ '{pg_item.description}'"
            )

        if errors:
            result.add_fail(f"Line item {mongo_id[:8]}...: {', '.join(errors)}")
        else:
            result.add_pass(f"Line item verified: {mongo_id[:8]}...")


def verify_all_line_items(mongo_db, db_session, result: VerificationResult):
    """Verify ALL line items field-by-field (thorough mode)"""
    logging.info("\n[4] Verifying ALL Line Items (Full Field-by-Field Check)")

    total = mongo_db[line_items_collection].count_documents({})
    logging.info(f"  Checking {total} line items...")

    if total == 0:
        result.add_warning("No line items in MongoDB")
        return

    # Build a lookup dict for PostgreSQL line items by mongo_id
    logging.info("  Building PostgreSQL lookup index...")
    pg_items_dict = {item.mongo_id: item for item in db_session.query(LineItem).all()}

    errors = []
    checked = 0
    last_log = 0

    for doc in mongo_db[line_items_collection].find():
        mongo_id = str(doc["_id"])
        pg_item = pg_items_dict.get(mongo_id)

        if not pg_item:
            errors.append(f"Missing in PostgreSQL: {mongo_id}")
            continue

        # Check ALL fields
        # 1. Amount
        if abs(float(pg_item.amount) - float(doc["amount"])) > 0.01:
            errors.append(f"{mongo_id}: amount {doc['amount']} ≠ {pg_item.amount}")

        # 2. Description
        if pg_item.description != doc.get("description", ""):
            errors.append(f"{mongo_id}: description mismatch")

        # 3. Date
        expected_date = datetime.fromtimestamp(float(doc.get("date", 0)), UTC)
        if pg_item.date != expected_date:
            errors.append(f"{mongo_id}: date {expected_date} ≠ {pg_item.date}")

        # 4. Payment method
        if pg_item.payment_method.name != doc.get("payment_method", ""):
            errors.append(
                f"{mongo_id}: payment_method '{doc.get('payment_method')}' ≠ '{pg_item.payment_method.name}'"
            )

        # 5. Notes
        expected_notes = doc.get("notes")
        if pg_item.notes != expected_notes:
            errors.append(f"{mongo_id}: notes mismatch")

        checked += 1

        # Progress logging every 1000 records
        if checked % 1000 == 0 and checked != last_log:
            logging.info(f"  Checked {checked}/{total}...")
            last_log = checked

    # Report results
    if errors:
        # Show first 20 errors
        for error in errors[:20]:
            result.add_fail(error)
        if len(errors) > 20:
            result.add_fail(f"... and {len(errors) - 20} more field mismatches")
    else:
        result.add_pass(f"All {checked} line items verified (all fields match)")


def verify_foreign_keys(db_session, result: VerificationResult):
    """Verify foreign key integrity"""
    logging.info("\n[5] Verifying Foreign Key Integrity")

    # Check line_items.transaction_id references valid transactions
    orphaned_items = (
        db_session.query(LineItem)
        .filter(~LineItem.transaction_id.in_(db_session.query(Transaction.id)))
        .count()
    )

    if orphaned_items == 0:
        result.add_pass("All line items have valid transaction_id")
    else:
        result.add_fail(f"{orphaned_items} line items with invalid transaction_id")

    # Check line_items.payment_method_id references valid payment methods
    orphaned_pms = (
        db_session.query(LineItem)
        .filter(~LineItem.payment_method_id.in_(db_session.query(PaymentMethod.id)))
        .count()
    )

    if orphaned_pms == 0:
        result.add_pass("All line items have valid payment_method_id")
    else:
        result.add_fail(f"{orphaned_pms} line items with invalid payment_method_id")


def verify_mongo_id_uniqueness(db_session, result: VerificationResult):
    """Verify mongo_id fields are unique"""
    logging.info("\n[6] Verifying mongo_id Uniqueness")

    # Check for duplicate mongo_ids in line_items
    from sqlalchemy import func

    duplicates = (
        db_session.query(
            LineItem.mongo_id, func.count(LineItem.mongo_id).label("count")
        )
        .filter(LineItem.mongo_id.isnot(None))
        .group_by(LineItem.mongo_id)
        .having(func.count(LineItem.mongo_id) > 1)
        .all()
    )

    if not duplicates:
        result.add_pass("All mongo_id values are unique")
    else:
        result.add_fail(
            f"Found {len(duplicates)} duplicate mongo_id values in line_items"
        )


def verify_transaction_dates(db_session, result: VerificationResult):
    """Verify transaction dates are reasonable"""
    logging.info("\n[7] Verifying Transaction Dates Range")

    # Check for transactions with invalid dates (too far in past/future)
    min_date = datetime(2000, 1, 1, tzinfo=UTC)
    max_date = datetime(2030, 1, 1, tzinfo=UTC)

    invalid_dates = (
        db_session.query(Transaction)
        .filter(
            (Transaction.transaction_date < min_date)
            | (Transaction.transaction_date > max_date)
        )
        .count()
    )

    if invalid_dates == 0:
        result.add_pass("All transaction dates are reasonable")
    else:
        result.add_warning(
            f"{invalid_dates} transactions with dates outside 2000-2030 range"
        )


def verify_no_extra_records(mongo_db, db_session, result: VerificationResult):
    """Verify PostgreSQL doesn't have extra records not in MongoDB (bidirectional check)"""
    logging.info("\n[8] Checking for Extra Records in PostgreSQL")

    # Get all mongo_ids from PostgreSQL
    logging.info("  Loading PostgreSQL mongo_ids...")
    pg_mongo_ids = {
        item.mongo_id
        for item in db_session.query(LineItem.mongo_id).all()
        if item.mongo_id
    }

    # Get all _ids from MongoDB
    logging.info("  Loading MongoDB _ids...")
    mongo_ids = {
        str(doc["_id"]) for doc in mongo_db[line_items_collection].find({}, {"_id": 1})
    }

    # Find extras in PostgreSQL
    extra_in_pg = pg_mongo_ids - mongo_ids

    if extra_in_pg:
        result.add_fail(
            f"Found {len(extra_in_pg)} line items in PostgreSQL not in MongoDB"
        )
        for mongo_id in list(extra_in_pg)[:5]:
            result.add_fail(f"  Extra in PostgreSQL: {mongo_id}")
        if len(extra_in_pg) > 5:
            result.add_fail(f"  ... and {len(extra_in_pg) - 5} more extra records")
    else:
        result.add_pass("No extra records in PostgreSQL")


def verify_transaction_dates_accurate(mongo_db, db_session, result: VerificationResult):
    """Verify transaction dates match source data exactly"""
    logging.info("\n[9] Verifying Transaction Date Accuracy")

    collections = {
        "stripe_raw_transaction_data": "stripe",
        "venmo_raw_data": "venmo",
        "splitwise_raw_data": "splitwise",
        "cash_raw_data": "cash",
    }

    errors = []
    checked = 0
    last_log = 0

    for collection_name, source in collections.items():
        for doc in mongo_db[collection_name].find():
            mongo_id = str(doc["_id"])
            pg_txn = (
                db_session.query(Transaction)
                .filter_by(source=source, source_id=mongo_id)
                .first()
            )

            if not pg_txn:
                continue

            # Calculate expected date based on source
            if source == "stripe":
                expected = datetime.fromtimestamp(
                    float(doc.get("transacted_at", 0)), UTC
                )
            elif source == "venmo":
                expected = datetime.fromtimestamp(
                    float(doc.get("date_created", 0)), UTC
                )
            elif source == "splitwise":
                iso_date = doc.get("date", "")
                posix_timestamp = iso_8601_to_posix(iso_date)
                expected = datetime.fromtimestamp(posix_timestamp, UTC)
            elif source == "cash":
                expected = datetime.fromtimestamp(float(doc.get("date", 0)), UTC)
            else:
                continue

            if pg_txn.transaction_date != expected:
                errors.append(f"{source}:{mongo_id[:8]}...")

            checked += 1
            if checked % 1000 == 0 and checked != last_log:
                logging.info(f"  Checked {checked} transactions...")
                last_log = checked

    if errors:
        for error in errors[:10]:
            result.add_fail(f"Date mismatch: {error}")
        if len(errors) > 10:
            result.add_fail(f"... and {len(errors) - 10} more date mismatches")
    else:
        result.add_pass(f"All {checked} transaction dates accurate")


def verify_payment_method_mappings(mongo_db, db_session, result: VerificationResult):
    """Verify all payment methods in line items exist and are mapped correctly"""
    logging.info("\n[10] Verifying Payment Method Mappings")

    # Get all unique payment methods from MongoDB
    mongo_payment_methods = mongo_db[line_items_collection].distinct("payment_method")

    # Get all payment methods from PostgreSQL
    pg_payment_methods = {pm.name for pm in db_session.query(PaymentMethod).all()}

    # Check for missing payment methods
    missing = set(mongo_payment_methods) - pg_payment_methods

    if missing:
        result.add_fail(f"Missing payment methods in PostgreSQL: {missing}")
    else:
        result.add_pass(f"All {len(mongo_payment_methods)} payment methods exist")

    # Verify mappings are correct (already checked in verify_all_line_items but good to confirm)
    logging.info("  Verifying payment method mappings...")
    mismatches = 0
    checked = 0

    for doc in mongo_db[line_items_collection].find():
        mongo_id = str(doc["_id"])
        pg_item = db_session.query(LineItem).filter_by(mongo_id=mongo_id).first()

        if pg_item and pg_item.payment_method.name != doc.get("payment_method"):
            mismatches += 1

        checked += 1
        if checked % 1000 == 0:
            logging.info(f"  Checked {checked} mappings...")

    if mismatches > 0:
        result.add_fail(
            f"{mismatches} line items with incorrect payment_method mapping"
        )
    else:
        result.add_pass(f"All {checked} payment method mappings correct")


def verify_aggregate_totals(mongo_db, db_session, result: VerificationResult):
    """Verify aggregate totals match by source (catches systematic errors)"""
    logging.info("\n[11] Verifying Aggregate Totals by Source")

    sources = ["venmo", "splitwise", "stripe", "cash"]

    for source in sources:
        # Build set of mongo_ids for this source from transactions
        pg_txns = db_session.query(Transaction).filter_by(source=source).all()
        source_txn_ids = {txn.id for txn in pg_txns}

        if not source_txn_ids:
            continue

        # PostgreSQL total for this source
        pg_total = db_session.query(func.sum(LineItem.amount)).filter(
            LineItem.transaction_id.in_(source_txn_ids)
        ).scalar() or Decimal(0)

        # MongoDB total - need to identify line items from this source
        # Line items have format "line_item_{transaction_mongo_id}"
        mongo_total = Decimal(0)
        count = 0

        # Get all transaction mongo_ids for this source
        source_mongo_ids = {txn.source_id for txn in pg_txns}

        for doc in mongo_db[line_items_collection].find():
            mongo_id = str(doc["_id"])
            # Extract transaction mongo_id from line item id
            if mongo_id.startswith("line_item_"):
                txn_mongo_id = mongo_id.replace("line_item_", "")
                if txn_mongo_id in source_mongo_ids:
                    mongo_total += Decimal(str(doc.get("amount", 0)))
                    count += 1

        if abs(mongo_total - pg_total) > Decimal("0.01"):
            result.add_fail(
                f"{source} totals: MongoDB ${mongo_total} ≠ PostgreSQL ${pg_total}"
            )
        else:
            result.add_pass(f"{source} totals match: ${pg_total} ({count} items)")


def main():
    """Main verification function"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Verify data consistency between MongoDB and PostgreSQL"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick verification mode (spot checks only, faster)",
    )
    parser.add_argument(
        "--thorough",
        action="store_true",
        help="Thorough verification mode (checks every record, slower)",
    )
    args = parser.parse_args()

    # Default to thorough if neither specified
    if not args.quick and not args.thorough:
        args.thorough = True

    # Cannot specify both
    if args.quick and args.thorough:
        logging.error("Cannot specify both --quick and --thorough")
        sys.exit(1)

    mode = "QUICK" if args.quick else "THOROUGH"
    logging.info("=" * 60)
    logging.info(f"Phase 3: Transaction & Line Item Verification ({mode} MODE)")
    logging.info("=" * 60)
    logging.info(f"MongoDB URI: {MONGO_URI}")
    logging.info(f"PostgreSQL URL: {DATABASE_URL}")
    logging.info("")

    # Connect to databases
    mongo_client = MongoClient(MONGO_URI)
    db_name = MONGO_URI.split("/")[-1]
    mongo_db = mongo_client[db_name]

    db_session = SessionLocal()
    result = VerificationResult()

    try:
        # Core checks (always run)
        verify_transaction_counts(mongo_db, db_session, result)
        verify_line_item_counts(mongo_db, db_session, result)

        # Transaction verification - quick or thorough
        if args.quick:
            verify_transaction_spot_checks(mongo_db, db_session, result)
        else:
            verify_all_transactions(mongo_db, db_session, result)

        # Line item verification - quick or thorough
        if args.quick:
            verify_line_item_spot_checks(mongo_db, db_session, result)
        else:
            verify_all_line_items(mongo_db, db_session, result)

        # Always run these
        verify_foreign_keys(db_session, result)
        verify_mongo_id_uniqueness(db_session, result)
        verify_transaction_dates(db_session, result)

        # Thorough mode - additional checks
        if args.thorough:
            verify_no_extra_records(mongo_db, db_session, result)
            verify_payment_method_mappings(mongo_db, db_session, result)
            verify_aggregate_totals(mongo_db, db_session, result)

        # Print summary
        success = result.print_summary()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    finally:
        db_session.close()
        mongo_client.close()


if __name__ == "__main__":
    main()
