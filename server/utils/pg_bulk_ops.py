"""
PostgreSQL Bulk Operations for Dual-Write

Shared bulk write functions for efficiently upserting transactions and line items
to PostgreSQL during the dual-write period.
"""

import json
import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from helpers import iso_8601_to_posix, to_dict_robust
from models.database import SessionLocal
from models.sql_models import BankAccount, Category, EventLineItem, LineItem, PaymentMethod, Transaction, User
from utils.id_generator import generate_id

logger = logging.getLogger(__name__)


def get_transaction_date(transaction: Dict[str, Any], source: str) -> datetime:
    """Extract transaction date based on source type."""
    if source == "venmo_api":
        posix_timestamp = float(transaction.get("date_created", 0))
        return datetime.fromtimestamp(posix_timestamp, UTC)
    elif source == "splitwise_api":
        iso_date = transaction.get("date", "")
        posix_timestamp = iso_8601_to_posix(iso_date)
        return datetime.fromtimestamp(posix_timestamp, UTC)
    elif source == "stripe_api":
        posix_timestamp = float(transaction.get("transacted_at", 0))
        return datetime.fromtimestamp(posix_timestamp, UTC)
    else:
        logger.warning(f"Unknown source type: {source}, using current time")
        return datetime.now(UTC)


def _normalize_source_data(source_data: Dict[str, Any]) -> Dict[str, Any]:
    """Round-trip through JSON so comparisons against stored JSON columns are type-stable."""
    return json.loads(json.dumps(source_data, default=str))


def bulk_upsert_transactions(db_session, transactions_source_data: List[Any], source: str) -> int:
    """
    Bulk upsert transactions to PostgreSQL.

    Inserts new transactions and updates source_data on existing ones when the
    external record changed (e.g. an edited Splitwise amount), so re-imports
    propagate upstream edits.

    Args:
        db_session: SQLAlchemy session
        transactions_source_data: List of transaction objects/dicts
        source: Transaction source type (venmo, splitwise, stripe, cash)

    Returns:
        Count of inserted and updated transactions
    """
    if not transactions_source_data:
        return 0

    transaction_dicts = []
    source_ids = []
    for txn in transactions_source_data:
        txn_dict = to_dict_robust(txn)

        # Ensure we have an 'id' field from various possible sources
        if "id" not in txn_dict:
            if hasattr(txn, "id"):
                txn_dict["id"] = str(txn.id)

        source_id = str(txn_dict.get("id", ""))
        if not source_id:
            logger.warning(f"Skipping transaction without id: {txn_dict}")
            continue

        source_ids.append((source, source_id))
        transaction_dicts.append(txn_dict)

    if not transaction_dicts:
        return 0

    existing_by_source_id = {
        txn.source_id: txn
        for txn in db_session.query(Transaction)
        .filter(Transaction.source == source, Transaction.source_id.in_([sid for _, sid in source_ids]))
        .all()
    }

    bulk_inserts = []
    updated_count = 0
    for txn_dict, (_, source_id) in zip(transaction_dicts, source_ids):
        transaction_date = get_transaction_date(txn_dict, source)
        source_data = _normalize_source_data({k: v for k, v in txn_dict.items() if k != "id"})

        existing = existing_by_source_id.get(source_id)
        if existing:
            if existing.source_data != source_data:
                existing.source_data = source_data
                existing.transaction_date = transaction_date
                updated_count += 1
            continue

        bulk_inserts.append(
            {
                "id": generate_id("txn"),
                "source": source,
                "source_id": source_id,
                "source_data": source_data,
                "transaction_date": transaction_date,
            }
        )

    if bulk_inserts:
        db_session.bulk_insert_mappings(Transaction, bulk_inserts)
        logger.info(f"Bulk inserted {len(bulk_inserts)} {source} transactions to PostgreSQL")
    if updated_count:
        logger.info(f"Updated {updated_count} changed {source} transactions in PostgreSQL")

    return len(bulk_inserts) + updated_count


def _convert_line_item_to_dict(li: Any) -> Optional[Dict[str, Any]]:
    """
    Convert a line item (object or dict) to a standardized dict format.

    Returns None if the line item format is unsupported.
    """
    if hasattr(li, "id") and hasattr(li, "date") and hasattr(li, "payment_method"):
        return {
            "id": li.id,
            "date": li.date,
            "payment_method": li.payment_method,
            "description": li.description,
            "amount": li.amount,
            "responsible_party": getattr(li, "responsible_party", ""),
            "source_id": getattr(li, "source_id", ""),
            "transaction_id": getattr(li, "transaction_id", ""),
        }
    elif isinstance(li, dict):
        return li.copy()
    else:
        logger.warning(f"Skipping unsupported line item type: {type(li)}")
        return None


def _parse_line_item_date(date_value: Any) -> datetime:
    if isinstance(date_value, (int, float)):
        return datetime.fromtimestamp(float(date_value), UTC)
    logger.warning(f"Unexpected date type: {type(date_value)}, using current time")
    return datetime.now(UTC)


def _parse_line_item_amount(amount_value: Any) -> Decimal:
    try:
        return Decimal(str(amount_value))
    except (ValueError, TypeError):
        logger.warning(f"Invalid amount: {amount_value}, using 0")
        return Decimal("0.00")


def _build_line_item_insert_mapping(
    li_dict: Dict[str, Any],
    transaction_id: str,
    payment_method_id: str,
) -> Dict[str, Any]:
    """Build bulk insert mapping for a single line item."""
    return {
        "id": generate_id("li"),
        "transaction_id": transaction_id,
        "date": _parse_line_item_date(li_dict.get("date", 0)),
        "amount": _parse_line_item_amount(li_dict.get("amount", 0)),
        "description": li_dict.get("description", ""),
        "payment_method_id": payment_method_id,
        "responsible_party": li_dict.get("responsible_party", ""),
        "notes": li_dict.get("notes"),
    }


def _dates_equal(a: Optional[datetime], b: Optional[datetime]) -> bool:
    """Compare datetimes treating naive values (e.g. from SQLite) as UTC."""
    if a is None or b is None:
        return a == b
    if a.tzinfo is None:
        a = a.replace(tzinfo=UTC)
    if b.tzinfo is None:
        b = b.replace(tzinfo=UTC)
    return a == b


def _update_line_item_if_changed(line_item: LineItem, li_dict: Dict[str, Any]) -> bool:
    """Apply external edits to an existing line item. Returns True if anything changed."""
    new_date = _parse_line_item_date(li_dict.get("date", 0))
    new_amount = _parse_line_item_amount(li_dict.get("amount", 0))
    new_description = li_dict.get("description", "")
    new_responsible_party = li_dict.get("responsible_party", "")

    if (
        line_item.amount == new_amount
        and line_item.description == new_description
        and (line_item.responsible_party or "") == new_responsible_party
        and _dates_equal(line_item.date, new_date)
    ):
        return False

    line_item.date = new_date
    line_item.amount = new_amount
    line_item.description = new_description
    line_item.responsible_party = new_responsible_party
    return True


def bulk_upsert_line_items(db_session, line_items_data: List[Any], source: str) -> int:
    """
    Bulk upsert line items to PostgreSQL.

    Process:
    1. Extracts source_id (external API ID) from incoming line items
    2. Looks up matching database transactions to get transaction_id (database FK)
    3. Checks for duplicates based on source_id to prevent re-importing
    4. Inserts line items with transaction_id (database FK) to maintain referential integrity

    Deduplication strategy: Uses source_id to ensure each external transaction
    only creates one line item, even if the same API data is imported multiple times.

    Args:
        db_session: SQLAlchemy session
        line_items_data: List of LineItem objects with source_id populated
        source: Transaction source type (venmo, splitwise, stripe, cash)

    Returns:
        Count of inserted line items
    """
    if not line_items_data:
        return 0

    payment_methods = db_session.query(PaymentMethod).all()
    payment_method_map = {pm.name: pm.id for pm in payment_methods}

    # Extract source IDs (external API IDs) from line items to find matching transactions
    line_item_source_ids = []
    for li in line_items_data:
        if hasattr(li, "source_id") and li.source_id:
            line_item_source_ids.append(li.source_id)
        elif isinstance(li, dict) and li.get("source_id"):
            line_item_source_ids.append(li.get("source_id"))

    if line_item_source_ids:
        transactions = (
            db_session.query(Transaction)
            .filter(
                Transaction.source == source,
                Transaction.source_id.in_(line_item_source_ids),
            )
            .all()
        )
        # Map external API ID (source_id) to database ID (txn.id)
        transaction_lookup = {txn.source_id: txn.id for txn in transactions}
    else:
        transaction_lookup = {}

    line_item_dicts = []
    source_ids_to_check = []
    for li in line_items_data:
        li_dict = _convert_line_item_to_dict(li)
        if not li_dict:
            continue

        source_id = li_dict.get("source_id", "")
        if source_id:
            source_ids_to_check.append(source_id)

        line_item_dicts.append(li_dict)

    if not line_item_dicts:
        return 0

    # Find line items that already exist for these transactions so re-imports
    # update them instead of creating duplicates.
    existing_line_items_by_source_id: Dict[str, LineItem] = {}
    evented_line_item_ids: set = set()
    if source_ids_to_check:
        rows = (
            db_session.query(LineItem, Transaction.source_id)
            .join(Transaction, Transaction.id == LineItem.transaction_id)
            .filter(Transaction.source == source, Transaction.source_id.in_(source_ids_to_check))
            .all()
        )
        existing_line_items_by_source_id = {row[1]: row[0] for row in rows}
        if existing_line_items_by_source_id:
            evented_line_item_ids = {
                row[0]
                for row in db_session.query(EventLineItem.line_item_id)
                .filter(EventLineItem.line_item_id.in_([li.id for li in existing_line_items_by_source_id.values()]))
                .all()
            }

    bulk_inserts = []
    updated_count = 0
    for li_dict in line_item_dicts:
        source_id = li_dict.get("source_id", "")

        existing_li = existing_line_items_by_source_id.get(source_id) if source_id else None
        if existing_li:
            # Propagate external edits, but never touch line items already reviewed into an event
            if existing_li.id not in evented_line_item_ids:
                updated_count += _update_line_item_if_changed(existing_li, li_dict)
            continue

        if not source_id:
            logger.warning(f"Skipping line item without source_id (source={source})")
            continue

        # Look up the database transaction ID using the external source ID
        transaction_id = transaction_lookup.get(source_id)
        if not transaction_id:
            logger.warning(f"Transaction not found for line item (source={source}, source_id={source_id})")
            continue

        payment_method_name = li_dict.get("payment_method", "Unknown")
        payment_method_id = payment_method_map.get(payment_method_name)

        if not payment_method_id:
            unknown_pm = db_session.query(PaymentMethod).filter_by(name="Unknown").first()
            if not unknown_pm:
                unknown_pm = PaymentMethod(id=generate_id("pm"), name="Unknown", type="cash", is_active=True)
                db_session.add(unknown_pm)
                db_session.flush()
                payment_method_map["Unknown"] = unknown_pm.id
            payment_method_id = unknown_pm.id

        bulk_inserts.append(_build_line_item_insert_mapping(li_dict, transaction_id, payment_method_id))

    if bulk_inserts:
        db_session.bulk_insert_mappings(LineItem, bulk_inserts)
        logger.info(f"Bulk inserted {len(bulk_inserts)} {source} line items to PostgreSQL")
    if updated_count:
        logger.info(f"Updated {updated_count} changed {source} line items in PostgreSQL")

    return len(bulk_inserts) + updated_count


def delete_transactions_for_removed_sources(db_session, source: str, source_ids: List[str]) -> int:
    """
    Delete transactions (and their line items) whose source records were deleted upstream.

    Transactions whose line item has already been reviewed into an event are kept
    and logged, so upstream deletions never silently alter events.

    Returns:
        Count of deleted transactions
    """
    if not source_ids:
        return 0

    transactions = (
        db_session.query(Transaction).filter(Transaction.source == source, Transaction.source_id.in_(source_ids)).all()
    )
    if not transactions:
        return 0

    line_items = db_session.query(LineItem).filter(LineItem.transaction_id.in_([txn.id for txn in transactions])).all()
    line_item_by_transaction_id = {li.transaction_id: li for li in line_items}
    evented_line_item_ids = (
        {
            row[0]
            for row in db_session.query(EventLineItem.line_item_id)
            .filter(EventLineItem.line_item_id.in_([li.id for li in line_items]))
            .all()
        }
        if line_items
        else set()
    )

    deleted_count = 0
    for txn in transactions:
        line_item = line_item_by_transaction_id.get(txn.id)
        if line_item and line_item.id in evented_line_item_ids:
            logger.warning(f"Keeping {source} transaction {txn.source_id} deleted upstream: its line item belongs to an event")
            continue
        if line_item:
            db_session.delete(line_item)
        db_session.delete(txn)
        deleted_count += 1

    if deleted_count:
        logger.info(f"Deleted {deleted_count} {source} transactions removed upstream")
    return deleted_count


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

    existing = db_session.query(BankAccount.id).filter(BankAccount.id.in_(account_ids)).all()
    existing_ids = {row[0] for row in existing}

    bulk_inserts = []
    bulk_updates = []
    for acc_dict in account_dicts:
        account_id = acc_dict.get("id")
        if not account_id:
            continue

        account_data = {
            "id": account_id,
            "institution_name": acc_dict.get("institution_name", ""),
            "display_name": acc_dict.get("display_name", ""),
            "last4": acc_dict.get("last4") or "",
            "status": acc_dict.get("status", "active"),
            "can_relink": acc_dict.get("can_relink", True),
        }

        if "currency" in acc_dict:
            account_data["currency"] = acc_dict["currency"]
        if "latest_balance" in acc_dict:
            account_data["latest_balance"] = Decimal(str(acc_dict["latest_balance"]))
        if "balance_as_of" in acc_dict:
            balance_as_of = acc_dict["balance_as_of"]
            if isinstance(balance_as_of, (int, float)):
                balance_as_of = datetime.fromtimestamp(balance_as_of, UTC)
            account_data["balance_as_of"] = balance_as_of

        if account_id in existing_ids:
            bulk_updates.append(account_data)
        else:
            bulk_inserts.append(account_data)

    count = 0
    if bulk_inserts:
        db_session.bulk_insert_mappings(BankAccount, bulk_inserts)
        logger.info(f"Bulk inserted {len(bulk_inserts)} bank accounts to PostgreSQL")
        count += len(bulk_inserts)

    if bulk_updates:
        db_session.bulk_update_mappings(BankAccount, bulk_updates)
        logger.info(f"Bulk updated {len(bulk_updates)} bank accounts to PostgreSQL")
        count += len(bulk_updates)

    return count


def _seed_default_categories(db_session: Any, user_id: str) -> None:
    """
    Seed default categories for a new user.

    Args:
        db_session: Database session
        user_id: User ID to create categories for
    """
    default_categories = [
        "Alcohol",
        "Dining",
        "Entertainment",
        "Groceries",
        "Hobbies",
        "Income",
        "Investment",
        "Medical",
        "Rent",
        "Shopping",
        "Subscription",
        "Transfer",
        "Transit",
        "Travel",
    ]

    for category_name in default_categories:
        category = Category(
            id=generate_id("cat"),
            user_id=user_id,
            name=category_name,
        )
        db_session.add(category)

    logger.info(f"Seeded {len(default_categories)} default categories for user {user_id}")


def upsert_user(user_data: Dict[str, Any]) -> bool:
    """
    Upsert a single user to PostgreSQL.
    Seeds default categories for new users.

    Args:
        user_data: User dict

    Returns:
        True if inserted, False if already exists
    """
    user_dict = to_dict_robust(user_data)
    user_id = user_dict.get("id")

    if not user_id:
        logger.warning("Cannot upsert user without id")
        raise ValueError("Cannot upsert user without id")

    with SessionLocal.begin() as db_session:
        existing = db_session.query(User).filter(User.id == user_id).first()
        if existing:
            return False

        user = User(
            id=user_id,
            first_name=user_dict.get("first_name", ""),
            last_name=user_dict.get("last_name", ""),
            email=user_dict.get("email", ""),
            password_hash=user_dict.get("password_hash", ""),
        )

        db_session.add(user)

        # Seed default categories for new user
        _seed_default_categories(db_session, user_id)

    return True
