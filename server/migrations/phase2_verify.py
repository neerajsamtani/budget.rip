#!/usr/bin/env python
"""
Phase 2 Verification Script

Verifies that all reference data (categories, payment methods, tags) was migrated correctly
from MongoDB to PostgreSQL.

Usage:
    python migrations/phase2_verify.py
"""

import sys
import os

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from pymongo import MongoClient

from constants import MONGO_URI, CATEGORIES
from models.database import SessionLocal
from models.sql_models import Category, PaymentMethod, Tag

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def verify_categories():
    """Verify categories migration."""
    logger.info("\n" + "=" * 60)
    logger.info("Verifying Categories")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        # Expected categories (excluding "All")
        expected_categories = [cat for cat in CATEGORIES if cat != "All"]
        expected_count = len(expected_categories)

        # Get PostgreSQL categories
        pg_categories = db.query(Category).all()
        pg_count = len(pg_categories)
        pg_category_names = {cat.name for cat in pg_categories}

        logger.info(f"\n📊 Category Counts:")
        logger.info(f"   Expected: {expected_count}")
        logger.info(f"   PostgreSQL: {pg_count}")

        # Check if counts match
        if pg_count != expected_count:
            logger.error(f"   ✗ Count mismatch!")
            return False

        logger.info(f"   ✓ Counts match")

        # Check for missing categories
        missing = set(expected_categories) - pg_category_names
        if missing:
            logger.error(f"\n   ✗ Missing categories: {missing}")
            return False

        # Check for extra categories
        extra = pg_category_names - set(expected_categories)
        if extra:
            logger.warning(
                f"\n   ⚠️  Extra categories (not in CATEGORIES constant): {extra}"
            )

        logger.info(f"\n   ✓ All expected categories present")

        # Show category details
        logger.info(f"\n📋 Category Details:")
        for cat in sorted(pg_categories, key=lambda x: x.name):
            active_str = "✓" if cat.is_active else "✗"
            logger.info(f"   [{active_str}] {cat.name:20s} {cat.id}")

        logger.info(f"\n✅ Category verification passed!")
        return True

    except Exception as e:
        logger.error(f"\n❌ Category verification failed: {e}")
        return False
    finally:
        db.close()


def verify_payment_methods():
    """Verify payment methods migration."""
    logger.info("\n" + "=" * 60)
    logger.info("Verifying Payment Methods")
    logger.info("=" * 60)

    # Connect to MongoDB
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client["flask_db"]

    db = SessionLocal()
    try:
        # Get MongoDB accounts and deduplicate (same logic as migration)
        all_accounts = list(mongo_db.accounts.find())
        from collections import defaultdict

        by_name = defaultdict(list)
        for acc in all_accounts:
            name = acc.get("display_name", acc.get("name", "Unknown"))
            by_name[name].append(acc)

        # Count unique accounts (prefer active)
        unique_accounts = []
        for name, accs in by_name.items():
            if len(accs) > 1:
                active = [a for a in accs if a.get("status") == "active"]
                unique_accounts.append(active[0] if active else accs[0])
            else:
                unique_accounts.append(accs[0])

        mongo_count = len(unique_accounts)
        mongo_total = len(all_accounts)
        pg_count = db.query(PaymentMethod).count()

        logger.info(f"\n📊 Payment Method Counts:")
        logger.info(f"   MongoDB accounts (total): {mongo_total}")
        logger.info(f"   MongoDB accounts (unique): {mongo_count}")
        logger.info(f"   PostgreSQL payment methods: {pg_count}")

        # Check if counts match
        if pg_count != mongo_count:
            logger.error(f"   ✗ Count mismatch!")
            return False

        logger.info(f"   ✓ Counts match")

        # Get all payment methods and group by type
        payment_methods = db.query(PaymentMethod).all()
        by_type = {}
        active_count = 0
        inactive_count = 0

        for pm in payment_methods:
            by_type.setdefault(pm.type, []).append(pm)
            if pm.is_active:
                active_count += 1
            else:
                inactive_count += 1

        logger.info(f"\n📊 Payment Method Status:")
        logger.info(f"   Active: {active_count}")
        logger.info(f"   Inactive: {inactive_count}")

        logger.info(f"\n📋 Payment Methods by Type:")
        for pm_type in sorted(by_type.keys()):
            pms = by_type[pm_type]
            logger.info(f"\n   {pm_type.upper()} ({len(pms)}):")
            for pm in sorted(pms, key=lambda x: x.name):
                active_str = "✓" if pm.is_active else "✗"
                external_id_str = (
                    f" [{pm.external_id[:20]}...]" if pm.external_id else ""
                )
                logger.info(
                    f"     [{active_str}] {pm.name:35s} {pm.id}{external_id_str}"
                )

        # Verify all MongoDB accounts have a corresponding PostgreSQL payment method
        logger.info(f"\n🔍 Checking MongoDB → PostgreSQL mapping:")
        mongo_accounts = list(mongo_db.accounts.find())
        pg_names = {pm.name for pm in payment_methods}

        missing_in_pg = []
        for account in mongo_accounts:
            name = account.get("display_name", account.get("name", "Unknown"))
            if name not in pg_names:
                missing_in_pg.append(name)

        if missing_in_pg:
            logger.error(
                f"   ✗ MongoDB accounts missing in PostgreSQL: {missing_in_pg}"
            )
            return False

        logger.info(f"   ✓ All MongoDB accounts found in PostgreSQL")

        logger.info(f"\n✅ Payment method verification passed!")
        return True

    except Exception as e:
        logger.error(f"\n❌ Payment method verification failed: {e}")
        return False
    finally:
        db.close()
        mongo_client.close()


def verify_tags():
    """Verify tags migration."""
    logger.info("\n" + "=" * 60)
    logger.info("Verifying Tags")
    logger.info("=" * 60)

    # Connect to MongoDB
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client["flask_db"]

    db = SessionLocal()
    try:
        # Get unique tags from MongoDB events
        events_with_tags = mongo_db.events.find(
            {"tags": {"$exists": True, "$ne": [], "$ne": None}}, {"tags": 1}
        )

        mongo_tags = set()
        for event in events_with_tags:
            if event.get("tags"):
                mongo_tags.update(event["tags"])

        mongo_count = len(mongo_tags)
        pg_count = db.query(Tag).count()
        pg_tags = db.query(Tag).all()
        pg_tag_names = {tag.name for tag in pg_tags}

        logger.info(f"\n📊 Tag Counts:")
        logger.info(f"   MongoDB unique tags: {mongo_count}")
        logger.info(f"   PostgreSQL tags: {pg_count}")

        # Check if counts match
        if pg_count != mongo_count:
            logger.error(f"   ✗ Count mismatch!")
            return False

        logger.info(f"   ✓ Counts match")

        # Check for missing tags
        missing = mongo_tags - pg_tag_names
        if missing:
            logger.error(f"\n   ✗ Missing tags: {missing}")
            return False

        # Check for extra tags
        extra = pg_tag_names - mongo_tags
        if extra:
            logger.warning(f"\n   ⚠️  Extra tags (not in MongoDB): {extra}")

        logger.info(f"\n   ✓ All MongoDB tags present")

        # Show tag details
        logger.info(f"\n📋 Tag Details:")
        for tag in sorted(pg_tags, key=lambda x: x.name):
            logger.info(f"   • {tag.name:25s} {tag.id}")

        logger.info(f"\n✅ Tag verification passed!")
        return True

    except Exception as e:
        logger.error(f"\n❌ Tag verification failed: {e}")
        return False
    finally:
        db.close()
        mongo_client.close()


def verify_all():
    """Run all verification checks."""
    logger.info("\n" + "=" * 70)
    logger.info("Phase 2: Reference Data Migration Verification")
    logger.info("=" * 70)

    results = {
        "categories": verify_categories(),
        "payment_methods": verify_payment_methods(),
        "tags": verify_tags(),
    }

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("Verification Summary")
    logger.info("=" * 70)

    all_passed = True
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"   {check:20s}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        logger.info(f"\n✅ All Phase 2 verifications passed!\n")
        return True
    else:
        logger.error(f"\n❌ Some Phase 2 verifications failed!\n")
        return False


if __name__ == "__main__":
    success = verify_all()
    sys.exit(0 if success else 1)
