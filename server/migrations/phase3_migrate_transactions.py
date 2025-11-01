#!/usr/bin/env python3
"""
Phase 3: Migrate Transactions from MongoDB to PostgreSQL

This script migrates raw transaction data from MongoDB collections to the PostgreSQL transactions table:
- venmo_raw_data -> transactions (source='venmo')
- splitwise_raw_data -> transactions (source='splitwise')
- stripe_raw_transaction_data -> transactions (source='stripe')
- cash_raw_data -> transactions (source='cash')

The script stores the original MongoDB _id in source_id and the full transaction
data in the source_data JSONB column for audit trail.
"""

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from sqlalchemy.exc import IntegrityError

from constants import DATABASE_URL, MONGO_URI
from helpers import iso_8601_to_posix
from models.database import SessionLocal
from models.sql_models import Transaction
from utils.id_generator import generate_id

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# MongoDB collection to source type mapping
COLLECTION_SOURCE_MAPPING = {
    "venmo_raw_data": "venmo",
    "splitwise_raw_data": "splitwise",
    "stripe_raw_transaction_data": "stripe",
    "cash_raw_data": "cash",
}


def get_transaction_date(transaction: Dict[str, Any], source: str) -> datetime:
    if source == "venmo":
        # Venmo stores date_created as POSIX timestamp
        posix_timestamp = float(transaction.get("date_created", 0))
        return datetime.fromtimestamp(posix_timestamp, UTC)

    elif source == "splitwise":
        # Splitwise stores date as ISO 8601 string
        iso_date = transaction.get("date", "")
        posix_timestamp = iso_8601_to_posix(iso_date)
        return datetime.fromtimestamp(posix_timestamp, UTC)

    elif source == "stripe":
        # Stripe stores transacted_at as POSIX timestamp (integer seconds)
        posix_timestamp = float(transaction.get("transacted_at", 0))
        return datetime.fromtimestamp(posix_timestamp, UTC)

    elif source == "cash":
        # Cash stores date as POSIX timestamp
        posix_timestamp = float(transaction.get("date", 0))
        return datetime.fromtimestamp(posix_timestamp, UTC)

    else:
        # Fallback to current time
        logging.warning(f"Unknown source type: {source}, using current time")
        return datetime.now(UTC)


def migrate_collection(
    mongo_db,
    collection_name: str,
    source: str,
    db_session,
    mongo_to_txn_map: Dict[str, str],
) -> int:
    """
    Migrate a single MongoDB collection to PostgreSQL transactions table.

    Args:
        mongo_db: MongoDB database instance
        collection_name: Name of the MongoDB collection
        source: Transaction source type (venmo, splitwise, stripe, cash)
        db_session: SQLAlchemy session
        mongo_to_txn_map: Dictionary to store mongo_id -> transaction_id mapping

    Returns:
        Number of transactions migrated
    """
    collection = mongo_db[collection_name]
    count = 0
    skipped = 0

    logging.info(f"Migrating {collection_name} (source={source})...")

    for doc in collection.find():
        mongo_id = str(doc["_id"])

        # Check if transaction already migrated (idempotent)
        existing = (
            db_session.query(Transaction)
            .filter_by(source=source, source_id=mongo_id)
            .first()
        )

        if existing:
            mongo_to_txn_map[f"{source}:{mongo_id}"] = existing.id
            skipped += 1
            continue

        # Generate new transaction ID
        txn_id = generate_id("txn")

        # Extract transaction date
        transaction_date = get_transaction_date(doc, source)

        # Create Transaction record
        # Remove MongoDB-specific _id from source_data
        source_data = {k: v for k, v in doc.items() if k != "_id"}

        transaction = Transaction(
            id=txn_id,
            source=source,
            source_id=mongo_id,
            source_data=source_data,
            transaction_date=transaction_date,
        )

        try:
            db_session.add(transaction)
            db_session.flush()  # Flush to catch constraint violations early

            # Store mapping for line items
            mongo_to_txn_map[f"{source}:{mongo_id}"] = txn_id
            count += 1

            if count % 100 == 0:
                db_session.commit()
                logging.info(
                    f"  Migrated {count} transactions from {collection_name}..."
                )

        except IntegrityError as e:
            logging.error(f"Error migrating transaction {mongo_id}: {e}")
            db_session.rollback()
            continue

    # Final commit
    db_session.commit()

    logging.info(
        f"✓ Migrated {count} transactions from {collection_name} (skipped {skipped} existing)"
    )
    return count


def migrate_all_transactions() -> Dict[str, str]:
    """
    Migrate all raw transactions from MongoDB to PostgreSQL.

    Returns:
        Dictionary mapping "source:mongo_id" -> transaction_id for line item migration
    """
    # Connect to MongoDB
    mongo_client = MongoClient(MONGO_URI)
    db_name = MONGO_URI.split("/")[-1]
    mongo_db = mongo_client[db_name]

    # Connect to PostgreSQL
    db_session = SessionLocal()

    # Track mongo_id to transaction_id mapping for line items
    mongo_to_txn_map: Dict[str, str] = {}

    try:
        total_count = 0

        # Migrate each collection
        for collection_name, source in COLLECTION_SOURCE_MAPPING.items():
            count = migrate_collection(
                mongo_db, collection_name, source, db_session, mongo_to_txn_map
            )
            total_count += count

        logging.info(f"\n{'='*60}")
        logging.info(f"✓ Successfully migrated {total_count} total transactions")
        logging.info(f"{'='*60}\n")

        # Verification
        verify_migration(db_session, mongo_db)

        return mongo_to_txn_map

    finally:
        db_session.close()
        mongo_client.close()


def verify_migration(db_session, mongo_db):
    """
    Verify that transaction counts match between MongoDB and PostgreSQL.
    """
    logging.info("\nVerifying migration...")

    for collection_name, source in COLLECTION_SOURCE_MAPPING.items():
        mongo_count = mongo_db[collection_name].count_documents({})
        pg_count = db_session.query(Transaction).filter_by(source=source).count()

        if mongo_count == pg_count:
            logging.info(
                f"  ✓ {collection_name}: {mongo_count} MongoDB = {pg_count} PostgreSQL"
            )
        else:
            logging.warning(
                f"  ✗ {collection_name}: {mongo_count} MongoDB ≠ {pg_count} PostgreSQL"
            )

    total_mongo = sum(
        mongo_db[coll].count_documents({}) for coll in COLLECTION_SOURCE_MAPPING.keys()
    )
    total_pg = db_session.query(Transaction).count()

    logging.info(f"\nTotal: {total_mongo} MongoDB = {total_pg} PostgreSQL")

    if total_mongo == total_pg:
        logging.info("✓ Verification passed!")
    else:
        logging.warning("✗ Verification failed - counts do not match")


if __name__ == "__main__":
    logging.info("Starting Phase 3: Transaction Migration")
    logging.info(f"MongoDB URI: {MONGO_URI}")
    logging.info(f"PostgreSQL URL: {DATABASE_URL}")
    logging.info("")

    # Run migration
    mongo_to_txn_map = migrate_all_transactions()

    # Save mapping to file for line items migration
    import json

    mapping_file = Path(__file__).parent / "phase3_transaction_mapping.json"
    with open(mapping_file, "w") as f:
        json.dump(mongo_to_txn_map, f, indent=2)

    logging.info(f"\nSaved transaction mapping to: {mapping_file}")
    logging.info("Ready for Phase 3 line items migration!")
