#!/usr/bin/env python
"""
Phase 2 Migration: Payment Methods

Migrates payment methods from MongoDB accounts collection to PostgreSQL.

The accounts are Stripe Financial Connections accounts with the following structure:
- id: Stripe ID (e.g., fca_1MGBX6FEgyBBpYpUDG4TylSG)
- display_name: Display name (e.g., "CHASE COLLEGE")
- category: cash, credit, other
- subcategory: checking, savings, credit_card, other
- institution_name: Bank name
- last4: Last 4 digits

Type mapping:
- category='credit' + subcategory='credit_card' → type='credit'
- category='cash' → type='bank'
- category='other' → type='bank'
- Manual accounts → type='cash'

Additionally, this script creates standard payment methods not in Stripe:
- Splitwise: For Splitwise expenses
- Venmo: For Venmo transactions
- Cash: For manual cash entries

Usage:
    python migrations/phase2_migrate_payment_methods.py
"""

import sys
import os

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from pymongo import MongoClient
from sqlalchemy.exc import IntegrityError

from constants import MONGO_URI
from models.database import SessionLocal
from models.sql_models import PaymentMethod
from utils.id_generator import generate_id

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def determine_payment_type(account):
    """
    Determine payment method type from Stripe account data.

    Args:
        account: MongoDB account document

    Returns:
        str: One of 'bank', 'credit', 'venmo', 'splitwise', 'cash'
    """
    category = account.get("category", "").lower()
    subcategory = account.get("subcategory", "").lower()

    # Credit cards
    if category == "credit" and subcategory == "credit_card":
        return "credit"

    # Cash accounts (checking, savings)
    if category == "cash":
        return "bank"

    # Default to bank
    return "bank"


def migrate_payment_methods():
    """
    Migrate payment methods from MongoDB accounts to PostgreSQL.

    Returns:
        dict: Mapping of payment method name to PostgreSQL ID
    """
    # Connect to MongoDB
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client["flask_db"]

    # Get all accounts and deduplicate by display_name
    all_accounts = list(mongo_db.accounts.find())
    logger.info(f"Found {len(all_accounts)} accounts in MongoDB")

    # Group by display_name and prefer active accounts
    from collections import defaultdict

    by_name = defaultdict(list)
    for acc in all_accounts:
        name = acc.get("display_name", acc.get("name", "Unknown"))
        by_name[name].append(acc)

    # For duplicates, prefer active accounts
    accounts = []
    duplicates_resolved = 0
    for name, accs in by_name.items():
        if len(accs) > 1:
            # Prefer active accounts
            active = [a for a in accs if a.get("status") == "active"]
            if active:
                accounts.append(active[0])
                duplicates_resolved += 1
                logger.info(
                    f"  Resolved duplicate '{name}': Using active account (id: {active[0]['id']})"
                )
            else:
                # All inactive, use first one
                accounts.append(accs[0])
                duplicates_resolved += 1
                logger.info(
                    f"  Resolved duplicate '{name}': Using first inactive account (id: {accs[0]['id']})"
                )
        else:
            accounts.append(accs[0])

    if duplicates_resolved > 0:
        logger.info(f"Resolved {duplicates_resolved} duplicate account names")
    logger.info(f"Processing {len(accounts)} unique accounts")

    db = SessionLocal()
    payment_method_map = {}

    try:
        migrated_count = 0
        skipped_count = 0

        for account in accounts:
            try:
                name = account.get("display_name", account.get("name", "Unknown"))
                external_id = account.get("id")
                payment_type = determine_payment_type(account)
                is_active = account.get("status", "active") == "active"

                # Check if payment method already exists
                existing = (
                    db.query(PaymentMethod).filter(PaymentMethod.name == name).first()
                )

                if existing:
                    logger.info(
                        f"  ⊙ Payment method already exists: {name} -> {existing.id}"
                    )
                    payment_method_map[name] = existing.id
                    skipped_count += 1
                    continue

                # Create new payment method
                payment_method = PaymentMethod(
                    id=generate_id("pm"),
                    name=name,
                    type=payment_type,
                    external_id=external_id,
                    is_active=is_active,
                )

                db.add(payment_method)
                db.flush()

                payment_method_map[name] = payment_method.id
                logger.info(
                    f"  ✓ Migrated: {name} ({payment_type}) -> {payment_method.id} "
                    f"[active: {is_active}]"
                )
                migrated_count += 1

            except IntegrityError as e:
                logger.warning(f"  ! Integrity error for {name}: {e}")
                db.rollback()

                # Try to get the existing record
                existing = (
                    db.query(PaymentMethod).filter(PaymentMethod.name == name).first()
                )
                if existing:
                    payment_method_map[name] = existing.id
                    skipped_count += 1

            except Exception as e:
                logger.error(f"  ✗ Error migrating {name}: {e}")
                db.rollback()
                raise

        # Commit all changes
        db.commit()

        logger.info(f"\n✅ Payment method migration complete!")
        logger.info(f"   Migrated: {migrated_count}")
        logger.info(f"   Skipped (already exist): {skipped_count}")
        logger.info(f"   Total in map: {len(payment_method_map)}")

        return payment_method_map

    except Exception as e:
        logger.error(f"\n❌ Payment method migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        mongo_client.close()


def create_standard_payment_methods():
    """
    Create standard payment methods that aren't in the Stripe accounts collection.

    These include:
    - Splitwise: For Splitwise expenses
    - Venmo: For Venmo transactions
    - Cash: For manual cash entries

    Returns:
        dict: Mapping of payment method name to PostgreSQL ID
    """
    db = SessionLocal()
    payment_method_map = {}

    # Standard payment methods not in Stripe Financial Connections
    standard_methods = [
        {"name": "Splitwise", "type": "splitwise"},
        {"name": "Venmo", "type": "venmo"},
        {"name": "Cash", "type": "cash"},
    ]

    try:
        logger.info(f"\n📝 Creating standard payment methods...")

        created_count = 0
        skipped_count = 0

        for method in standard_methods:
            # Check if already exists
            existing = db.query(PaymentMethod).filter_by(name=method["name"]).first()

            if existing:
                logger.info(f"  ⊙ {method['name']} already exists -> {existing.id}")
                payment_method_map[method["name"]] = existing.id
                skipped_count += 1
            else:
                pm = PaymentMethod(
                    id=generate_id("pm"),
                    name=method["name"],
                    type=method["type"],
                    is_active=True,
                )
                db.add(pm)
                db.flush()
                payment_method_map[method["name"]] = pm.id
                logger.info(
                    f"  ✓ Created {method['name']} ({method['type']}) -> {pm.id}"
                )
                created_count += 1

        db.commit()

        logger.info(f"\n✅ Standard payment methods complete!")
        logger.info(f"   Created: {created_count}")
        logger.info(f"   Skipped (already exist): {skipped_count}")

        return payment_method_map

    except Exception as e:
        logger.error(f"\n❌ Standard payment methods failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_migration():
    """Verify that all payment methods were migrated correctly."""
    # Connect to MongoDB
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client["flask_db"]

    db = SessionLocal()
    try:
        # Get unique account names from MongoDB (after deduplication logic)
        all_accounts = list(mongo_db.accounts.find())
        from collections import defaultdict

        by_name = defaultdict(list)
        for acc in all_accounts:
            name = acc.get("display_name", acc.get("name", "Unknown"))
            by_name[name].append(acc)
        unique_account_count = len(by_name)

        pg_count = db.query(PaymentMethod).count()

        # Standard payment methods that should exist
        standard_methods = ["Splitwise", "Venmo", "Cash"]

        logger.info(f"\n📊 Verification:")
        logger.info(f"   MongoDB accounts (raw): {len(all_accounts)}")
        logger.info(f"   MongoDB accounts (unique): {unique_account_count}")
        logger.info(f"   Standard payment methods: {len(standard_methods)}")
        logger.info(f"   PostgreSQL payment methods: {pg_count}")

        # Check that required standard payment methods exist
        missing_methods = []
        for method_name in standard_methods:
            exists = db.query(PaymentMethod).filter_by(name=method_name).first()
            if not exists:
                missing_methods.append(method_name)

        if missing_methods:
            logger.warning(
                f"   ⚠️  Missing required payment methods: {', '.join(missing_methods)}"
            )
            return False

        logger.info(f"   ✓ All required payment methods present")

        # Show all payment methods
        logger.info(f"\n   Payment Methods in PostgreSQL:")
        payment_methods = db.query(PaymentMethod).all()

        # Group by type
        by_type = {}
        for pm in payment_methods:
            by_type.setdefault(pm.type, []).append(pm)

        for pm_type, pms in sorted(by_type.items()):
            logger.info(f"\n     {pm_type.upper()}:")
            for pm in sorted(pms, key=lambda x: x.name):
                active_status = "✓" if pm.is_active else "✗"
                logger.info(f"       [{active_status}] {pm.name} ({pm.id})")

        return True

    finally:
        db.close()
        mongo_client.close()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Phase 2: Migrate Payment Methods")
    logger.info("=" * 60)

    # Run migration from MongoDB accounts
    payment_method_map = migrate_payment_methods()

    # Create standard payment methods (Splitwise, Venmo, Cash)
    standard_method_map = create_standard_payment_methods()

    # Verify
    success = verify_migration()

    if success:
        logger.info(f"\n✅ Phase 2 (Payment Methods) completed successfully!\n")
        sys.exit(0)
    else:
        logger.error(f"\n❌ Phase 2 (Payment Methods) verification failed!\n")
        sys.exit(1)
