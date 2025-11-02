"""
PostgreSQL Bulk Operations for Dual-Write

Shared bulk write functions for efficiently upserting transactions and line items
to PostgreSQL during the dual-write period.
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Dict, List

from helpers import iso_8601_to_posix, to_dict_robust
from models.sql_models import BankAccount, LineItem, PaymentMethod, Transaction, User
from utils.id_generator import generate_id

logger = logging.getLogger(__name__)


def get_transaction_date(transaction: Dict[str, Any], source: str) -> datetime:
    """Extract transaction date based on source type."""
    if source == "venmo":
        posix_timestamp = float(transaction.get("date_created", 0))
        return datetime.fromtimestamp(posix_timestamp, UTC)
    elif source == "splitwise":
        iso_date = transaction.get("date", "")
        posix_timestamp = iso_8601_to_posix(iso_date)
        return datetime.fromtimestamp(posix_timestamp, UTC)
    elif source == "stripe":
        posix_timestamp = float(transaction.get("transacted_at", 0))
        return datetime.fromtimestamp(posix_timestamp, UTC)
    elif source == "cash":
        posix_timestamp = float(transaction.get("date", 0))
        return datetime.fromtimestamp(posix_timestamp, UTC)
    else:
        logger.warning(f"Unknown source type: {source}, using current time")
        return datetime.now(UTC)


def bulk_upsert_transactions(
    db_session, transactions_data: List[Any], source: str
) -> int:
    """
    Bulk upsert transactions to PostgreSQL.

    Args:
        db_session: SQLAlchemy session
        transactions_data: List of transaction objects/dicts
        source: Transaction source type (venmo, splitwise, stripe, cash)

    Returns:
        Count of inserted transactions
    """
    if not transactions_data:
        return 0

    # Convert to dicts and extract MongoDB _id
    transaction_dicts = []
    mongo_ids = []
    for txn in transactions_data:
        # Convert to dict using robust conversion (handles both dict and object types)
        txn_dict = to_dict_robust(txn)

        # Ensure _id field is set correctly
        if "_id" not in txn_dict:
            if "id" in txn_dict:
                txn_dict["_id"] = txn_dict["id"]
            elif hasattr(txn, "_id"):
                txn_dict["_id"] = str(txn._id)
            elif hasattr(txn, "id"):
                txn_dict["_id"] = str(txn.id)

        mongo_id = str(txn_dict.get("_id", ""))
        if not mongo_id:
            logger.warning(f"Skipping transaction without _id: {txn_dict}")
            continue

        mongo_ids.append((source, mongo_id))
        transaction_dicts.append(txn_dict)

    if not transaction_dicts:
        return 0

    # Check existing transactions to avoid duplicates
    existing_query = db_session.query(Transaction.source, Transaction.source_id).filter(
        Transaction.source == source
    )
    if mongo_ids:
        existing_pairs = set(
            (row.source, row.source_id)
            for row in existing_query.filter(
                Transaction.source_id.in_([mid for _, mid in mongo_ids])
            ).all()
        )
    else:
        existing_pairs = set()

    # Prepare bulk insert mappings for new transactions
    bulk_inserts = []
    for txn_dict, (src, mongo_id) in zip(transaction_dicts, mongo_ids):
        if (src, mongo_id) in existing_pairs:
            continue

        transaction_date = get_transaction_date(txn_dict, source)

        # Remove MongoDB-specific _id from source_data
        source_data = {k: v for k, v in txn_dict.items() if k != "_id"}

        bulk_inserts.append(
            {
                "id": generate_id("txn"),
                "source": source,
                "source_id": mongo_id,
                "source_data": source_data,
                "transaction_date": transaction_date,
            }
        )

    if bulk_inserts:
        db_session.bulk_insert_mappings(Transaction, bulk_inserts)
        logger.info(
            f"Bulk inserted {len(bulk_inserts)} {source} transactions to PostgreSQL"
        )
        return len(bulk_inserts)

    return 0


def bulk_upsert_line_items(db_session, line_items_data: List[Any], source: str) -> int:
    """
    Bulk upsert line items to PostgreSQL.

    Args:
        db_session: SQLAlchemy session
        line_items_data: List of LineItem objects
        source: Transaction source type (venmo, splitwise, stripe, cash)

    Returns:
        Count of inserted line items
    """
    if not line_items_data:
        return 0

    # Pre-load payment method name-to-ID mapping
    payment_methods = db_session.query(PaymentMethod).all()
    payment_method_map = {pm.name: pm.id for pm in payment_methods}

    # Pre-build transaction lookup dict by (source, source_id)
    # Extract mongo_ids from line items to find matching transactions
    line_item_mongo_ids = []
    for li in line_items_data:
        if hasattr(li, "id"):
            li_id = li.id
        elif isinstance(li, dict):
            li_id = li.get("id", "")
        else:
            continue

        # Extract transaction mongo_id from line item id format: "line_item_{txn_mongo_id}"
        if li_id.startswith("line_item_"):
            txn_mongo_id = li_id.replace("line_item_", "")
            line_item_mongo_ids.append(txn_mongo_id)

    # Query transactions for this source
    if line_item_mongo_ids:
        transactions = (
            db_session.query(Transaction)
            .filter(
                Transaction.source == source,
                Transaction.source_id.in_(line_item_mongo_ids),
            )
            .all()
        )
        transaction_lookup = {txn.source_id: txn.id for txn in transactions}
    else:
        transaction_lookup = {}

    # Convert line items to dict format and check for existing
    line_item_dicts = []
    line_item_mongo_ids_check = []
    for li in line_items_data:
        # Handle LineItem objects (from resources.line_item)
        if hasattr(li, "id") and hasattr(li, "date") and hasattr(li, "payment_method"):
            li_dict = {
                "id": li.id,
                "date": li.date,
                "payment_method": li.payment_method,
                "description": li.description,
                "amount": li.amount,
                "responsible_party": getattr(li, "responsible_party", ""),
            }
        elif isinstance(li, dict):
            li_dict = li.copy()
        else:
            logger.warning(f"Skipping unsupported line item type: {type(li)}")
            continue

        # Extract mongo_id from line item id
        li_id = li_dict.get("id", "")
        if li_id.startswith("line_item_"):
            txn_mongo_id = li_id.replace("line_item_", "")
            line_item_mongo_ids_check.append(f"line_item_{txn_mongo_id}")
            li_dict["_mongo_id"] = f"line_item_{txn_mongo_id}"
            li_dict["_txn_mongo_id"] = txn_mongo_id
        else:
            logger.warning(f"Skipping line item with unexpected id format: {li_id}")
            continue

        line_item_dicts.append(li_dict)

    if not line_item_dicts:
        return 0

    # Check existing line items by mongo_id
    existing_mongo_ids = set()
    if line_item_mongo_ids_check:
        existing = (
            db_session.query(LineItem.mongo_id)
            .filter(LineItem.mongo_id.in_(line_item_mongo_ids_check))
            .all()
        )
        existing_mongo_ids = {row[0] for row in existing}

    # Prepare bulk insert mappings
    bulk_inserts = []
    for li_dict in line_item_dicts:
        mongo_id = li_dict.get("_mongo_id", "")
        if mongo_id in existing_mongo_ids:
            continue

        txn_mongo_id = li_dict.get("_txn_mongo_id", "")
        transaction_id = transaction_lookup.get(txn_mongo_id)

        if not transaction_id:
            logger.warning(
                f"Transaction not found for line item {mongo_id} (source={source}, txn_mongo_id={txn_mongo_id})"
            )
            continue

        payment_method_name = li_dict.get("payment_method", "Unknown")
        payment_method_id = payment_method_map.get(payment_method_name)

        if not payment_method_id:
            # Create "Unknown" payment method if not found
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

        # Convert date and amount
        date_value = li_dict.get("date", 0)
        if isinstance(date_value, (int, float)):
            li_date = datetime.fromtimestamp(float(date_value), UTC)
        else:
            logger.warning(
                f"Unexpected date type: {type(date_value)}, using current time"
            )
            li_date = datetime.now(UTC)

        amount_value = li_dict.get("amount", 0)
        try:
            li_amount = Decimal(str(amount_value))
        except (ValueError, TypeError):
            logger.warning(f"Invalid amount: {amount_value}, using 0")
            li_amount = Decimal("0.00")

        bulk_inserts.append(
            {
                "id": generate_id("li"),
                "transaction_id": transaction_id,
                "mongo_id": mongo_id,
                "date": li_date,
                "amount": li_amount,
                "description": li_dict.get("description", ""),
                "payment_method_id": payment_method_id,
                "responsible_party": li_dict.get("responsible_party", ""),
                "notes": li_dict.get("notes"),
            }
        )

    if bulk_inserts:
        db_session.bulk_insert_mappings(LineItem, bulk_inserts)
        logger.info(
            f"Bulk inserted {len(bulk_inserts)} {source} line items to PostgreSQL"
        )
        return len(bulk_inserts)

    return 0


def bulk_upsert_bank_accounts(db_session, accounts_data: List[Any]) -> int:
    """
    Bulk upsert bank accounts to PostgreSQL.

    Args:
        db_session: SQLAlchemy session
        accounts_data: List of account dicts

    Returns:
        Count of inserted/updated accounts
    """
    if not accounts_data:
        return 0

    account_dicts = [to_dict_robust(acc) for acc in accounts_data]
    account_ids = [acc.get("id") for acc in account_dicts if acc.get("id")]

    if not account_ids:
        return 0

    # Check existing accounts
    existing = (
        db_session.query(BankAccount.id).filter(BankAccount.id.in_(account_ids)).all()
    )
    existing_ids = {row[0] for row in existing}

    # Prepare bulk inserts for new accounts
    bulk_inserts = []
    for acc_dict in account_dicts:
        account_id = acc_dict.get("id")
        if not account_id or account_id in existing_ids:
            continue

        bulk_inserts.append(
            {
                "id": account_id,
                "mongo_id": str(acc_dict.get("_id", "")),
                "institution_name": acc_dict.get("institution_name", ""),
                "display_name": acc_dict.get("display_name", ""),
                "last4": acc_dict.get("last4", ""),
                "status": acc_dict.get("status", "active"),
            }
        )

    if bulk_inserts:
        db_session.bulk_insert_mappings(BankAccount, bulk_inserts)
        logger.info(f"Bulk inserted {len(bulk_inserts)} bank accounts to PostgreSQL")
        return len(bulk_inserts)

    return 0


def upsert_user(db_session, user_data: Dict[str, Any]) -> bool:
    """
    Upsert a single user to PostgreSQL.

    Args:
        db_session: SQLAlchemy session
        user_data: User dict

    Returns:
        True if inserted, False if already exists
    """
    user_dict = to_dict_robust(user_data)
    user_id = user_dict.get("id")

    if not user_id:
        logger.warning("Cannot upsert user without id")
        return False

    # Check if user exists
    existing = db_session.query(User).filter(User.id == user_id).first()
    if existing:
        return False

    # Create new user
    user = User(
        id=user_id,
        mongo_id=str(user_dict.get("_id", "")),
        first_name=user_dict.get("first_name", ""),
        last_name=user_dict.get("last_name", ""),
        email=user_dict.get("email", ""),
        password_hash=user_dict.get("password_hash", ""),
    )

    db_session.add(user)
    logger.info(f"Inserted user {user_id} to PostgreSQL")
    return True
