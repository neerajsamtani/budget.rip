#!/usr/bin/env python3
"""
Phase 3: Reconciliation Script for Dual-Write Failures

This script reconciles data between MongoDB and PostgreSQL during the dual-write
period (Phases 3-5). It finds and syncs records that failed to write to PostgreSQL.

Purpose:
- Handle dual-write failures where MongoDB write succeeded but PostgreSQL failed
- Can be run as a cron job (e.g., hourly) during the migration period
- Ensures eventual consistency between databases

Usage:
    python migrations/phase3_reconcile.py [--dry-run]

    --dry-run: Show what would be synced without making changes
"""

import argparse
import logging
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from sqlalchemy.exc import IntegrityError

from constants import DATABASE_URL, MONGO_URI
from dao import line_items_collection
from helpers import iso_8601_to_posix
from models.database import SessionLocal
from models.sql_models import LineItem, PaymentMethod, Transaction
from utils.id_generator import generate_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class ReconciliationStats:
    """Track reconciliation statistics"""

    def __init__(self):
        self.transactions_synced = 0
        self.line_items_synced = 0
        self.errors = 0
        self.skipped = 0

    def print_summary(self):
        """Print reconciliation summary"""
        print("\n" + "="*60)
        print("RECONCILIATION SUMMARY")
        print("="*60)
        print(f"Transactions synced: {self.transactions_synced}")
        print(f"Line items synced:   {self.line_items_synced}")
        print(f"Skipped (exists):    {self.skipped}")
        print(f"Errors:              {self.errors}")
        print("="*60)


def get_transaction_date(transaction: Dict[str, Any], source: str) -> datetime:
    """Extract transaction date from raw data based on source type"""
    if source == 'venmo':
        posix_timestamp = float(transaction.get('date_created', 0))
        return datetime.fromtimestamp(posix_timestamp, UTC)

    elif source == 'splitwise':
        iso_date = transaction.get('date', '')
        posix_timestamp = iso_8601_to_posix(iso_date)
        return datetime.fromtimestamp(posix_timestamp, UTC)

    elif source == 'stripe':
        posix_timestamp = float(transaction.get('created', 0))
        return datetime.fromtimestamp(posix_timestamp, UTC)

    elif source == 'cash':
        posix_timestamp = float(transaction.get('date', 0))
        return datetime.fromtimestamp(posix_timestamp, UTC)

    else:
        return datetime.now(UTC)


def reconcile_transactions(
    mongo_db,
    db_session,
    stats: ReconciliationStats,
    dry_run: bool = False
) -> Dict[str, str]:
    """
    Reconcile transactions between MongoDB and PostgreSQL.

    Returns:
        Mapping of "source:mongo_id" -> transaction_id for line items
    """
    collections = {
        'venmo_raw_data': 'venmo',
        'splitwise_raw_data': 'splitwise',
        'stripe_raw_transaction_data': 'stripe',
        'cash_raw_data': 'cash',
    }

    mongo_to_txn_map: Dict[str, str] = {}

    logging.info("\n[1] Reconciling Transactions")

    for collection_name, source in collections.items():
        collection = mongo_db[collection_name]

        # Get all existing PostgreSQL transaction source_ids for this source
        existing_pg_ids: Set[str] = set(
            row[0] for row in db_session.query(Transaction.source_id).filter_by(
                source=source
            ).all()
        )

        # Find MongoDB docs not in PostgreSQL
        missing_count = 0

        for doc in collection.find():
            mongo_id = str(doc['_id'])

            if mongo_id in existing_pg_ids:
                # Already in PostgreSQL, build mapping
                pg_txn = db_session.query(Transaction).filter_by(
                    source=source,
                    source_id=mongo_id
                ).first()
                if pg_txn:
                    mongo_to_txn_map[f"{source}:{mongo_id}"] = pg_txn.id
                stats.skipped += 1
                continue

            # Missing from PostgreSQL - sync it
            missing_count += 1

            if dry_run:
                logging.info(
                    f"  [DRY RUN] Would sync {source} transaction: {mongo_id[:16]}..."
                )
                continue

            # Create transaction in PostgreSQL
            txn_id = generate_id('txn')
            transaction_date = get_transaction_date(doc, source)

            # Remove MongoDB _id from source_data
            source_data = {k: v for k, v in doc.items() if k != '_id'}

            transaction = Transaction(
                id=txn_id,
                source=source,
                source_id=mongo_id,
                source_data=source_data,
                transaction_date=transaction_date,
            )

            try:
                db_session.add(transaction)
                db_session.flush()

                mongo_to_txn_map[f"{source}:{mongo_id}"] = txn_id
                stats.transactions_synced += 1

                logging.info(f"  ✓ Synced {source} transaction: {mongo_id[:16]}...")

            except IntegrityError as e:
                logging.error(f"  ✗ Failed to sync transaction {mongo_id}: {e}")
                db_session.rollback()
                stats.errors += 1

        if missing_count > 0:
            logging.info(f"  Found {missing_count} missing {source} transactions")

        # Commit after each collection
        if not dry_run:
            db_session.commit()

    return mongo_to_txn_map


def reconcile_line_items(
    mongo_db,
    db_session,
    mongo_to_txn_map: Dict[str, str],
    stats: ReconciliationStats,
    dry_run: bool = False
):
    """Reconcile line items between MongoDB and PostgreSQL"""
    logging.info("\n[2] Reconciling Line Items")

    collection = mongo_db[line_items_collection]

    # Get all existing PostgreSQL mongo_ids
    existing_pg_ids: Set[str] = set(
        row[0] for row in db_session.query(LineItem.mongo_id).filter(
            LineItem.mongo_id.isnot(None)
        ).all()
    )

    # Get payment method mapping
    payment_methods = db_session.query(PaymentMethod).all()
    pm_map = {pm.name: pm.id for pm in payment_methods}

    missing_count = 0

    for doc in collection.find():
        mongo_id = str(doc['_id'])

        if mongo_id in existing_pg_ids:
            stats.skipped += 1
            continue

        # Missing from PostgreSQL - sync it
        missing_count += 1

        if dry_run:
            logging.info(f"  [DRY RUN] Would sync line item: {mongo_id[:16]}...")
            continue

        # Find transaction_id
        transaction_id = None

        # Line items use format "line_item_{transaction_mongo_id}"
        if mongo_id.startswith('line_item_'):
            txn_mongo_id = mongo_id.replace('line_item_', '')

            # Try each source
            for source in ['venmo', 'splitwise', 'stripe', 'cash']:
                key = f"{source}:{txn_mongo_id}"
                if key in mongo_to_txn_map:
                    transaction_id = mongo_to_txn_map[key]
                    break

        # If no transaction found, create manual transaction
        if not transaction_id:
            txn_id = generate_id('txn')
            transaction = Transaction(
                id=txn_id,
                source='manual',
                source_id=f"manual_{mongo_id}",
                source_data={
                    'description': doc.get('description', 'Manual entry'),
                    'amount': doc.get('amount', 0),
                    'note': 'Created by reconciliation for orphaned line item'
                },
                transaction_date=datetime.fromtimestamp(
                    float(doc.get('date', 0)), UTC
                ),
            )

            try:
                db_session.add(transaction)
                db_session.flush()
                transaction_id = txn_id
            except IntegrityError as e:
                logging.error(f"  ✗ Failed to create manual transaction: {e}")
                db_session.rollback()
                stats.errors += 1
                continue

        # Look up payment method
        payment_method_name = doc.get('payment_method', 'Unknown')
        payment_method_id = pm_map.get(payment_method_name)

        if not payment_method_id:
            # Create Unknown payment method if needed
            unknown_pm = db_session.query(PaymentMethod).filter_by(
                name='Unknown'
            ).first()

            if not unknown_pm:
                unknown_pm = PaymentMethod(
                    id=generate_id('pm'),
                    name='Unknown',
                    type='cash',
                    is_active=True
                )
                db_session.add(unknown_pm)
                db_session.flush()
                pm_map['Unknown'] = unknown_pm.id

            payment_method_id = pm_map['Unknown']

        # Create line item
        line_item = LineItem(
            id=generate_id('li'),
            transaction_id=transaction_id,
            mongo_id=mongo_id,
            date=datetime.fromtimestamp(float(doc.get('date', 0)), UTC),
            amount=Decimal(str(doc.get('amount', 0))),
            description=doc.get('description', ''),
            payment_method_id=payment_method_id,
            notes=doc.get('notes'),
        )

        try:
            db_session.add(line_item)
            db_session.flush()

            stats.line_items_synced += 1
            logging.info(f"  ✓ Synced line item: {mongo_id[:16]}...")

        except IntegrityError as e:
            logging.error(f"  ✗ Failed to sync line item {mongo_id}: {e}")
            db_session.rollback()
            stats.errors += 1

        # Commit every 100 items
        if stats.line_items_synced % 100 == 0:
            db_session.commit()

    # Final commit
    if not dry_run:
        db_session.commit()

    if missing_count > 0:
        logging.info(f"  Found {missing_count} missing line items")


def main():
    """Main reconciliation function"""
    parser = argparse.ArgumentParser(
        description='Reconcile MongoDB and PostgreSQL data during dual-write period'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be synced without making changes'
    )
    args = parser.parse_args()

    logging.info("="*60)
    logging.info("Phase 3: Reconciliation Script")
    if args.dry_run:
        logging.info("[DRY RUN MODE - No changes will be made]")
    logging.info("="*60)
    logging.info(f"MongoDB URI: {MONGO_URI}")
    logging.info(f"PostgreSQL URL: {DATABASE_URL}")
    logging.info("")

    # Connect to databases
    mongo_client = MongoClient(MONGO_URI)
    db_name = MONGO_URI.split('/')[-1]
    mongo_db = mongo_client[db_name]

    db_session = SessionLocal()
    stats = ReconciliationStats()

    try:
        # Reconcile transactions first
        mongo_to_txn_map = reconcile_transactions(
            mongo_db,
            db_session,
            stats,
            dry_run=args.dry_run
        )

        # Then reconcile line items
        reconcile_line_items(
            mongo_db,
            db_session,
            mongo_to_txn_map,
            stats,
            dry_run=args.dry_run
        )

        # Print summary
        stats.print_summary()

        if args.dry_run:
            logging.info("\n[DRY RUN] No changes were made")

    finally:
        db_session.close()
        mongo_client.close()


if __name__ == '__main__':
    main()
