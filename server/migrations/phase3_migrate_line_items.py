#!/usr/bin/env python3
"""
Phase 3: Migrate Line Items from MongoDB to PostgreSQL

This script migrates line items from MongoDB to PostgreSQL:
- Stores original MongoDB _id in mongo_id column for ID coexistence
- Links to transactions via transaction_id foreign key
- Looks up payment_method_id by name
- Creates manual Transaction records for orphaned line items

Prerequisites:
- Run phase3_migrate_transactions.py first to create transaction_mapping.json
- Payment methods must be migrated (Phase 2)
"""

import json
import logging
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from sqlalchemy.exc import IntegrityError

from constants import MONGO_URI, get_database_display_url
from dao import line_items_collection
from models.database import SessionLocal
from models.sql_models import LineItem, PaymentMethod, Transaction
from utils.id_generator import generate_id

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def load_transaction_mapping() -> Dict[str, str]:
    """
    Load the transaction mapping file created by phase3_migrate_transactions.py

    Returns:
        Dictionary mapping "source:mongo_id" -> transaction_id
    """
    mapping_file = Path(__file__).parent / "phase3_transaction_mapping.json"

    if not mapping_file.exists():
        raise FileNotFoundError(
            f"Transaction mapping file not found: {mapping_file}\n"
            "Please run phase3_migrate_transactions.py first!"
        )

    with open(mapping_file, "r") as f:
        return json.load(f)


def get_payment_method_map(db_session) -> Dict[str, str]:
    """
    Get mapping of payment method name -> id

    Args:
        db_session: SQLAlchemy session

    Returns:
        Dictionary mapping payment method name to ID
    """
    payment_methods = db_session.query(PaymentMethod).all()
    return {pm.name: pm.id for pm in payment_methods}


def create_manual_transaction(db_session, line_item_data: Dict[str, Any]) -> str:
    """
    Create a manual transaction for orphaned line items.

    Args:
        db_session: SQLAlchemy session
        line_item_data: Line item data from MongoDB

    Returns:
        Transaction ID
    """
    txn_id = generate_id("txn")
    mongo_id = str(line_item_data["_id"])

    # Create manual transaction
    transaction = Transaction(
        id=txn_id,
        source="manual",
        source_id=f"manual_{mongo_id}",
        source_data={
            "description": line_item_data.get("description", "Manual entry"),
            "amount": line_item_data.get("amount", 0),
            "payment_method": line_item_data.get("payment_method", "Unknown"),
            "note": "Created automatically for orphaned line item during migration",
        },
        transaction_date=datetime.fromtimestamp(
            float(line_item_data.get("date", 0)), UTC
        ),
    )

    db_session.add(transaction)
    db_session.flush()

    logging.info(
        f"  Created manual transaction {txn_id} for orphaned line item {mongo_id}"
    )
    return txn_id


def find_transaction_for_line_item(
    line_item_data: Dict[str, Any], transaction_mapping: Dict[str, str], db_session
) -> Optional[str]:
    """
    Find the transaction ID for a line item.

    Tries multiple strategies:
    1. Look up in transaction mapping by source
    2. Create manual transaction for orphaned items

    Args:
        line_item_data: Line item data from MongoDB
        transaction_mapping: Mapping from phase3_migrate_transactions
        db_session: SQLAlchemy session

    Returns:
        Transaction ID or None
    """
    mongo_id = str(line_item_data["_id"])

    # Line items use the format "line_item_{transaction_mongo_id}"
    # Extract the transaction mongo_id
    if mongo_id.startswith("line_item_"):
        txn_mongo_id = mongo_id.replace("line_item_", "")

        # Try each source type
        for source in ["venmo", "splitwise", "stripe", "cash"]:
            key = f"{source}:{txn_mongo_id}"
            if key in transaction_mapping:
                return transaction_mapping[key]

    # If we can't find a transaction, create a manual one
    return create_manual_transaction(db_session, line_item_data)


def migrate_line_items(
    mongo_db,
    db_session,
    transaction_mapping: Dict[str, str],
    payment_method_map: Dict[str, str],
) -> int:
    """
    Migrate line items from MongoDB to PostgreSQL.

    Args:
        mongo_db: MongoDB database instance
        db_session: SQLAlchemy session
        transaction_mapping: Mapping of source:mongo_id -> transaction_id
        payment_method_map: Mapping of payment method name -> id

    Returns:
        Number of line items migrated
    """
    collection = mongo_db[line_items_collection]
    committed_count = 0  # Only counts successfully committed items
    skipped = 0
    pending_in_batch = 0  # Uncommitted items in current batch

    total_items = collection.count_documents({})
    logging.info(f"Migrating {total_items} line items from MongoDB...")

    for doc in collection.find():
        mongo_id = str(doc["_id"])

        # Check if already migrated (idempotent)
        existing = db_session.query(LineItem).filter_by(mongo_id=mongo_id).first()

        if existing:
            skipped += 1
            continue

        # Find or create transaction
        # This always returns a transaction_id or raises an exception
        transaction_id = find_transaction_for_line_item(
            doc, transaction_mapping, db_session
        )

        # Look up payment method
        payment_method_name = doc.get("payment_method", "Unknown")
        payment_method_id = payment_method_map.get(payment_method_name)

        if not payment_method_id:
            logging.warning(
                f"Payment method '{payment_method_name}' not found for line item {mongo_id}, "
                "using 'Unknown'"
            )
            # Try to find or create Unknown payment method
            unknown_pm = (
                db_session.query(PaymentMethod).filter_by(name="Unknown").first()
            )
            if not unknown_pm:
                unknown_pm = PaymentMethod(
                    id=generate_id("pm"), name="Unknown", type="cash", is_active=True
                )
                db_session.add(unknown_pm)
                db_session.flush()
                payment_method_map["Unknown"] = unknown_pm.id
            payment_method_id = unknown_pm.id

        # Create LineItem
        line_item = LineItem(
            id=generate_id("li"),
            transaction_id=transaction_id,
            mongo_id=mongo_id,
            date=datetime.fromtimestamp(float(doc.get("date", 0)), UTC),
            amount=Decimal(str(doc.get("amount", 0))),
            description=doc.get("description", ""),
            payment_method_id=payment_method_id,
            notes=doc.get("notes"),
            responsible_party=doc.get("responsible_party"),
        )

        try:
            db_session.add(line_item)
            pending_in_batch += 1

            # Commit every 100 items
            if pending_in_batch >= 100:
                db_session.commit()
                committed_count += pending_in_batch
                logging.info(
                    f"  Migrated {committed_count}/{total_items} line items..."
                )
                pending_in_batch = 0

        except IntegrityError as e:
            logging.error(f"Error migrating line item {mongo_id}: {e}")
            db_session.rollback()
            # Rollback undoes all pending items in the current batch
            pending_in_batch = 0
            continue

    # Final commit of remaining items
    if pending_in_batch > 0:
        db_session.commit()
        committed_count += pending_in_batch

    logging.info(f"\n{'='*60}")
    logging.info(
        f"✓ Migrated {committed_count} line items (skipped {skipped} existing)"
    )
    logging.info(f"{'='*60}\n")

    return committed_count


def verify_migration(db_session, mongo_db):
    """
    Verify that line item counts match between MongoDB and PostgreSQL.
    """
    logging.info("\nVerifying migration...")

    mongo_count = mongo_db[line_items_collection].count_documents({})
    pg_count = db_session.query(LineItem).count()

    logging.info(f"  MongoDB line items: {mongo_count}")
    logging.info(f"  PostgreSQL line items: {pg_count}")

    if mongo_count == pg_count:
        logging.info("✓ Verification passed!")
    else:
        logging.warning("✗ Verification failed - counts do not match")

    # Check for orphaned transactions
    manual_txn_count = db_session.query(Transaction).filter_by(source="manual").count()
    if manual_txn_count > 0:
        logging.info(
            f"  Created {manual_txn_count} manual transactions for orphaned line items"
        )


def main():
    logging.info("Starting Phase 3: Line Items Migration")
    logging.info(f"MongoDB URI: {MONGO_URI}")
    logging.info(f"PostgreSQL URL: {get_database_display_url()}")
    logging.info("")

    # Load transaction mapping
    transaction_mapping = load_transaction_mapping()
    logging.info(f"Loaded {len(transaction_mapping)} transaction mappings\n")

    # Connect to MongoDB
    mongo_client = MongoClient(MONGO_URI)
    db_name = MONGO_URI.split("/")[-1]
    mongo_db = mongo_client[db_name]

    # Connect to PostgreSQL
    db_session = SessionLocal()

    try:
        # Get payment method mapping
        payment_method_map = get_payment_method_map(db_session)
        logging.info(f"Found {len(payment_method_map)} payment methods\n")

        # Migrate line items
        migrate_line_items(
            mongo_db, db_session, transaction_mapping, payment_method_map
        )

        # Verify migration
        verify_migration(db_session, mongo_db)

    finally:
        db_session.close()
        mongo_client.close()


if __name__ == "__main__":
    main()
