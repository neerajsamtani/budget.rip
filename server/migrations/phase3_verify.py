#!/usr/bin/env python3
"""
Phase 3: Verification Script for Transactions and Line Items

This script verifies data consistency between MongoDB and PostgreSQL after
Phase 3 migration. It performs:
1. Count verification for transactions and line items
2. Spot checks to compare field values
3. Foreign key integrity checks
4. Detailed error reporting

Run this script:
- After initial migration (phase3_migrate_*.py)
- Periodically during dual-write period (e.g., hourly cron job)
- Before switching reads to PostgreSQL (Phase 5)
"""

import logging
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient

from constants import DATABASE_URL, MONGO_URI
from dao import line_items_collection
from models.database import SessionLocal
from models.sql_models import LineItem, PaymentMethod, Transaction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        print(f"Passed:   {self.passed}")
        print(f"Failed:   {self.failed}")
        print(f"Warnings: {self.warnings}")

        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")

        print("="*60)

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
        'venmo_raw_data': 'venmo',
        'splitwise_raw_data': 'splitwise',
        'stripe_raw_transaction_data': 'stripe',
        'cash_raw_data': 'cash',
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
    total_mongo = sum(
        mongo_db[coll].count_documents({})
        for coll in collections.keys()
    )
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
    """Spot check transaction data integrity"""
    logging.info("\n[3] Spot Checking Transactions (10 random samples)")

    collections = {
        'venmo_raw_data': 'venmo',
        'splitwise_raw_data': 'splitwise',
        'stripe_raw_transaction_data': 'stripe',
        'cash_raw_data': 'cash',
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
            mongo_id = str(doc['_id'])

            # Find in PostgreSQL
            pg_txn = db_session.query(Transaction).filter_by(
                source=source,
                source_id=mongo_id
            ).first()

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


def verify_line_item_spot_checks(mongo_db, db_session, result: VerificationResult):
    """Spot check line item data integrity"""
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
        mongo_id = str(doc['_id'])

        # Find in PostgreSQL
        pg_item = db_session.query(LineItem).filter_by(mongo_id=mongo_id).first()

        if not pg_item:
            result.add_fail(f"Line item not found in PostgreSQL: {mongo_id}")
            continue

        # Verify fields match
        errors = []

        # Amount
        if abs(float(pg_item.amount) - float(doc['amount'])) > 0.01:
            errors.append(
                f"Amount mismatch: {doc['amount']} ≠ {pg_item.amount}"
            )

        # Description
        if pg_item.description != doc.get('description', ''):
            errors.append(
                f"Description mismatch: '{doc.get('description')}' ≠ '{pg_item.description}'"
            )

        if errors:
            result.add_fail(f"Line item {mongo_id[:8]}...: {', '.join(errors)}")
        else:
            result.add_pass(f"Line item verified: {mongo_id[:8]}...")


def verify_foreign_keys(db_session, result: VerificationResult):
    """Verify foreign key integrity"""
    logging.info("\n[5] Verifying Foreign Key Integrity")

    # Check line_items.transaction_id references valid transactions
    orphaned_items = db_session.query(LineItem).filter(
        ~LineItem.transaction_id.in_(
            db_session.query(Transaction.id)
        )
    ).count()

    if orphaned_items == 0:
        result.add_pass("All line items have valid transaction_id")
    else:
        result.add_fail(f"{orphaned_items} line items with invalid transaction_id")

    # Check line_items.payment_method_id references valid payment methods
    orphaned_pms = db_session.query(LineItem).filter(
        ~LineItem.payment_method_id.in_(
            db_session.query(PaymentMethod.id)
        )
    ).count()

    if orphaned_pms == 0:
        result.add_pass("All line items have valid payment_method_id")
    else:
        result.add_fail(f"{orphaned_pms} line items with invalid payment_method_id")


def verify_mongo_id_uniqueness(db_session, result: VerificationResult):
    """Verify mongo_id fields are unique"""
    logging.info("\n[6] Verifying mongo_id Uniqueness")

    # Check for duplicate mongo_ids in line_items
    from sqlalchemy import func

    duplicates = db_session.query(
        LineItem.mongo_id,
        func.count(LineItem.mongo_id).label('count')
    ).filter(
        LineItem.mongo_id.isnot(None)
    ).group_by(
        LineItem.mongo_id
    ).having(
        func.count(LineItem.mongo_id) > 1
    ).all()

    if not duplicates:
        result.add_pass("All mongo_id values are unique")
    else:
        result.add_fail(
            f"Found {len(duplicates)} duplicate mongo_id values in line_items"
        )


def verify_transaction_dates(db_session, result: VerificationResult):
    """Verify transaction dates are reasonable"""
    logging.info("\n[7] Verifying Transaction Dates")

    from datetime import datetime, UTC

    # Check for transactions with invalid dates (too far in past/future)
    min_date = datetime(2000, 1, 1, tzinfo=UTC)
    max_date = datetime(2030, 1, 1, tzinfo=UTC)

    invalid_dates = db_session.query(Transaction).filter(
        (Transaction.transaction_date < min_date) |
        (Transaction.transaction_date > max_date)
    ).count()

    if invalid_dates == 0:
        result.add_pass("All transaction dates are reasonable")
    else:
        result.add_warning(
            f"{invalid_dates} transactions with dates outside 2000-2030 range"
        )


def main():
    """Main verification function"""
    logging.info("="*60)
    logging.info("Phase 3: Transaction & Line Item Verification")
    logging.info("="*60)
    logging.info(f"MongoDB URI: {MONGO_URI}")
    logging.info(f"PostgreSQL URL: {DATABASE_URL}")
    logging.info("")

    # Connect to databases
    mongo_client = MongoClient(MONGO_URI)
    db_name = MONGO_URI.split('/')[-1]
    mongo_db = mongo_client[db_name]

    db_session = SessionLocal()
    result = VerificationResult()

    try:
        # Run verification checks
        verify_transaction_counts(mongo_db, db_session, result)
        verify_line_item_counts(mongo_db, db_session, result)
        verify_transaction_spot_checks(mongo_db, db_session, result)
        verify_line_item_spot_checks(mongo_db, db_session, result)
        verify_foreign_keys(db_session, result)
        verify_mongo_id_uniqueness(db_session, result)
        verify_transaction_dates(db_session, result)

        # Print summary
        success = result.print_summary()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    finally:
        db_session.close()
        mongo_client.close()


if __name__ == '__main__':
    main()
