#!/usr/bin/env python3
"""
Phase 5.5 Verification Script

Verifies that bank_accounts and users have been properly migrated from MongoDB
to PostgreSQL and can be read via the new read functions.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient

from constants import MONGO_URI
from dao import bank_accounts_collection, users_collection
from models.database import SessionLocal
from models.sql_models import BankAccount, User

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def verify_bank_accounts() -> bool:
    """Verify bank accounts migration"""
    logger.info("\n" + "=" * 60)
    logger.info("Verifying Bank Accounts")
    logger.info("=" * 60)

    success = True

    # Connect to MongoDB
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client["flask_db"]
    mongo_collection = mongo_db[bank_accounts_collection]

    # Connect to PostgreSQL
    db_session = SessionLocal()

    try:
        # Count totals
        mongo_count = mongo_collection.count_documents({})
        pg_count = db_session.query(BankAccount).count()

        logger.info(f"\nCounts:")
        logger.info(f"  MongoDB: {mongo_count}")
        logger.info(f"  PostgreSQL: {pg_count}")

        if pg_count == 0 and mongo_count > 0:
            logger.warning(
                "  ⚠️  No bank accounts in PostgreSQL but MongoDB has data. "
                "Run phase5_5_migrate_accounts_users.py to migrate."
            )
            success = False
        elif pg_count == mongo_count:
            logger.info("  ✅ Counts match")
        else:
            logger.warning(
                f"  ⚠️  Count mismatch: PostgreSQL has {pg_count}, MongoDB has {mongo_count}"
            )

        # Sample verification
        if mongo_count > 0:
            logger.info(f"\nSample verification:")
            sample = mongo_collection.find_one()
            if sample:
                sample_id = sample.get("id")
                pg_account = (
                    db_session.query(BankAccount)
                    .filter(BankAccount.id == sample_id)
                    .first()
                )

                if pg_account:
                    logger.info(f"  ✅ Sample account {sample_id} exists in PostgreSQL")
                    logger.info(
                        f"     Display name: {pg_account.display_name} (matches: {sample.get('display_name') == pg_account.display_name})"
                    )
                else:
                    logger.warning(
                        f"  ⚠️  Sample account {sample_id} not in PostgreSQL"
                    )
                    success = False

    except Exception as e:
        logger.error(f"❌ Error verifying bank accounts: {e}")
        success = False
    finally:
        db_session.close()
        mongo_client.close()

    return success


def verify_users() -> bool:
    """Verify users migration"""
    logger.info("\n" + "=" * 60)
    logger.info("Verifying Users")
    logger.info("=" * 60)

    success = True

    # Connect to MongoDB
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client["flask_db"]
    mongo_collection = mongo_db[users_collection]

    # Connect to PostgreSQL
    db_session = SessionLocal()

    try:
        # Count totals
        mongo_count = mongo_collection.count_documents({})
        pg_count = db_session.query(User).count()

        logger.info(f"\nCounts:")
        logger.info(f"  MongoDB: {mongo_count}")
        logger.info(f"  PostgreSQL: {pg_count}")

        if pg_count == 0 and mongo_count > 0:
            logger.warning(
                "  ⚠️  No users in PostgreSQL but MongoDB has data. "
                "Run phase5_5_migrate_accounts_users.py to migrate."
            )
            success = False
        elif pg_count == mongo_count:
            logger.info("  ✅ Counts match")
        else:
            logger.warning(
                f"  ⚠️  Count mismatch: PostgreSQL has {pg_count}, MongoDB has {mongo_count}"
            )

        # Sample verification - find a user with a valid email
        if mongo_count > 0:
            logger.info(f"\nSample verification:")
            sample = mongo_collection.find_one({"email": {"$exists": True, "$ne": ""}})
            if sample:
                sample_email = sample.get("email")
                pg_user = (
                    db_session.query(User).filter(User.email == sample_email).first()
                )

                if pg_user:
                    logger.info(f"  ✅ Sample user {sample_email} exists in PostgreSQL")
                    logger.info(f"     Name: {pg_user.first_name} {pg_user.last_name}")
                else:
                    logger.warning(
                        f"  ⚠️  Sample user {sample_email} not in PostgreSQL"
                    )
                    success = False
            else:
                logger.info("  ⚠️  No users with email found for sample verification")
                # Check by count instead
                if pg_count == mongo_count and pg_count > 0:
                    logger.info("  ✅ Counts match, migration appears successful")

    except Exception as e:
        logger.error(f"❌ Error verifying users: {e}")
        success = False
    finally:
        db_session.close()
        mongo_client.close()

    return success


def main():
    logger.info("=" * 60)
    logger.info("Phase 5.5 Verification")
    logger.info("=" * 60)

    results = {
        "bank_accounts": verify_bank_accounts(),
        "users": verify_users(),
    }

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Verification Summary")
    logger.info("=" * 60)

    all_passed = all(results.values())

    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{component}: {status}")

    if all_passed:
        logger.info("\n✅ Phase 5.5 verification complete - all checks passed!")
        return 0
    else:
        logger.warning(
            "\n⚠️  Some verification checks failed. Review the output above."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
