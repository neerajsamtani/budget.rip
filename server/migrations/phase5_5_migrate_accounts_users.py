#!/usr/bin/env python3
"""
Phase 5.5: Migrate Bank Accounts and Users from MongoDB to PostgreSQL

This script migrates:
- accounts collection -> bank_accounts table
- users collection -> users table

Both tables include mongo_id column for ID coexistence during migration.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from sqlalchemy.exc import IntegrityError

from constants import MONGO_URI
from dao import bank_accounts_collection, users_collection
from models.database import SessionLocal
from models.sql_models import BankAccount, User
from utils.id_generator import generate_id

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def migrate_bank_accounts(mongo_db, db_session) -> int:
    """Migrate bank accounts from MongoDB to PostgreSQL."""
    collection = mongo_db[bank_accounts_collection]
    migrated = 0
    skipped = 0

    logger.info(f"Migrating bank accounts...")
    total = collection.count_documents({})
    logger.info(f"  Total accounts in MongoDB: {total}")

    for account in collection.find():
        try:
            account_id = account.get("id")
            mongo_id = str(account["_id"])

            # Check if already migrated
            existing = db_session.query(BankAccount).filter(
                (BankAccount.id == account_id) | (BankAccount.mongo_id == mongo_id)
            ).first()

            if existing:
                skipped += 1
                continue

            # Create new bank account
            bank_account = BankAccount(
                id=account_id,
                mongo_id=mongo_id,
                institution_name=account.get("institution_name", ""),
                display_name=account.get("display_name", ""),
                last4=account.get("last4", ""),
                status=account.get("status", "active"),
            )

            db_session.add(bank_account)
            migrated += 1

            if migrated % 100 == 0:
                db_session.flush()
                logger.info(f"  Migrated {migrated} accounts...")

        except IntegrityError as e:
            logger.warning(f"  Integrity error for account {account_id}: {e}")
            db_session.rollback()
            skipped += 1
        except Exception as e:
            logger.error(f"  Error migrating account {account_id}: {e}")
            db_session.rollback()
            raise

    db_session.commit()
    logger.info(f"✅ Bank accounts migration complete: {migrated} migrated, {skipped} skipped")
    return migrated


def migrate_users(mongo_db, db_session) -> int:
    """Migrate users from MongoDB to PostgreSQL."""
    collection = mongo_db[users_collection]
    migrated = 0
    skipped = 0

    logger.info(f"Migrating users...")
    total = collection.count_documents({})
    logger.info(f"  Total users in MongoDB: {total}")

    for user_doc in collection.find():
        try:
            mongo_id = str(user_doc["_id"])
            # Generate ID if not present in MongoDB document
            user_id = user_doc.get("id") or generate_id("user")

            # Check if already migrated
            existing = db_session.query(User).filter(
                (User.id == user_id) | (User.mongo_id == mongo_id)
            ).first()

            if existing:
                skipped += 1
                continue

            # Create new user
            user = User(
                id=user_id,
                mongo_id=mongo_id,
                first_name=user_doc.get("first_name", ""),
                last_name=user_doc.get("last_name", ""),
                email=user_doc.get("email", ""),
                password_hash=user_doc.get("password_hash", ""),
            )

            db_session.add(user)
            migrated += 1

        except IntegrityError as e:
            logger.warning(f"  Integrity error for user {user_id}: {e}")
            db_session.rollback()
            skipped += 1
        except Exception as e:
            logger.error(f"  Error migrating user {user_id}: {e}")
            db_session.rollback()
            raise

    db_session.commit()
    logger.info(f"✅ Users migration complete: {migrated} migrated, {skipped} skipped")
    return migrated


def main():
    logger.info("=" * 60)
    logger.info("Phase 5.5: Migrate Bank Accounts and Users")
    logger.info("=" * 60)

    # Connect to MongoDB
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client["flask_db"]

    # Connect to PostgreSQL
    db_session = SessionLocal()

    try:
        # Migrate bank accounts
        accounts_migrated = migrate_bank_accounts(mongo_db, db_session)

        # Migrate users
        users_migrated = migrate_users(mongo_db, db_session)

        logger.info("\n" + "=" * 60)
        logger.info("Migration Summary")
        logger.info("=" * 60)
        logger.info(f"Bank Accounts migrated: {accounts_migrated}")
        logger.info(f"Users migrated: {users_migrated}")
        logger.info("✅ Phase 5.5 migration complete!")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        db_session.rollback()
        raise
    finally:
        db_session.close()
        mongo_client.close()


if __name__ == "__main__":
    main()
