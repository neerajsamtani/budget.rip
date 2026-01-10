import logging
from datetime import timezone as tz
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import joinedload, subqueryload

logger = logging.getLogger(__name__)

venmo_raw_data_collection: str = "venmo_raw_data"
splitwise_raw_data_collection: str = "splitwise_raw_data"
manual_raw_data_collection: str = "manual_raw_data"
stripe_raw_transaction_data_collection: str = "stripe_raw_transaction_data"
stripe_raw_account_data_collection: str = "stripe_raw_account_data"
line_items_collection: str = "line_items"
events_collection: str = "events"
bank_accounts_collection: str = "accounts"
users_collection: str = "users"
test_collection: str = "test_data"


def remove_event_from_line_item(line_item_id: Union[str, int]) -> None:
    """
    Remove event association from a line item by its ID.
    """
    from models.database import SessionLocal
    from models.sql_models import EventLineItem, LineItem

    try:
        with SessionLocal.begin() as db:
            line_item = db.query(LineItem).filter(LineItem.id == str(line_item_id)).first()
            if line_item:
                db.query(EventLineItem).filter(EventLineItem.line_item_id == line_item.id).delete()
            else:
                logger.warning(f"Could not find line item with ID {line_item_id}")
    except Exception:
        logger.error(f"Failed to remove event from line item: {line_item_id}")
        raise


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    from models.database import SessionLocal
    from models.sql_models import User

    with SessionLocal.begin() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "password_hash": user.password_hash,
        }


# TODO: Remove this router function and let callers use the underlying functions directly
def upsert(cur_collection_str: str, item: Dict[str, Any]) -> None:
    """Upsert item to PostgreSQL for migrated collections"""
    from models.database import SessionLocal

    try:
        with SessionLocal.begin() as db:
            # PostgreSQL write for transaction collections
            if cur_collection_str in [
                venmo_raw_data_collection,
                splitwise_raw_data_collection,
                stripe_raw_transaction_data_collection,
                manual_raw_data_collection,
            ]:
                from utils.pg_bulk_ops import _bulk_upsert_transactions

                source_map = {
                    venmo_raw_data_collection: "venmo_api",
                    splitwise_raw_data_collection: "splitwise_api",
                    stripe_raw_transaction_data_collection: "stripe_api",
                    manual_raw_data_collection: "manual",
                }
                source = source_map[cur_collection_str]
                _bulk_upsert_transactions(db, [item], source=source)

            elif cur_collection_str == bank_accounts_collection:
                from utils.pg_bulk_ops import _bulk_upsert_bank_accounts

                _bulk_upsert_bank_accounts(db, [item])

            elif cur_collection_str == line_items_collection:
                from utils.pg_bulk_ops import _bulk_upsert_line_items

                # Derive source from payment_method if not explicitly provided
                payment_method = item.get("payment_method", "manual").lower()
                source_map = {
                    "venmo": "venmo_api",
                    "splitwise": "splitwise_api",
                    "credit card": "stripe_api",
                    "debit card": "stripe_api",
                    "cash": "manual",
                }
                source = source_map.get(payment_method, "manual")
                _bulk_upsert_line_items(db, [item], source=source)

            else:
                raise NotImplementedError(f"Collection {cur_collection_str} not supported for upsert")
    except Exception as e:
        logger.error(f"Failed to upsert item to {cur_collection_str}: {e}")
        raise


def get_categorized_data() -> List[Dict[str, Any]]:
    """Group totalExpense by month, year, and category"""
    from sqlalchemy import extract, func

    from models.database import SessionLocal
    from models.sql_models import Category, Event, LineItem

    with SessionLocal.begin() as db:
        results = (
            db.query(
                extract("year", Event.date).label("year"),
                extract("month", Event.date).label("month"),
                Category.name.label("category"),
                func.sum(LineItem.amount).label("totalExpense"),
            )
            .join(Event.category)
            .join(Event.line_items)
            .group_by(extract("year", Event.date), extract("month", Event.date), Category.name)
            .order_by("year", "month", Category.name)
            .all()
        )

        return [
            {
                "year": int(row.year) if row.year else 0,
                "month": int(row.month) if row.month else 0,
                "category": row.category,
                "totalExpense": float(row.totalExpense) if row.totalExpense else 0.0,
            }
            for row in results
        ]


def _serialize_datetime(dt: Optional[Any]) -> float:
    """Treats naive datetimes from SQLite as UTC to ensure consistent timestamp conversion"""
    if not dt:
        return 0.0

    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz.utc).timestamp()
    else:
        return dt.timestamp()


def _pg_serialize_line_item(li: Any) -> Dict[str, Any]:
    """Convert LineItem ORM to dict"""
    # Determine if this is a manual transaction based on the source
    is_manual = li.transaction.source == "manual" if li.transaction else False

    data = {
        "id": li.id,
        "date": _serialize_datetime(li.date),
        "payment_method": li.payment_method.name if li.payment_method else "Unknown",
        "description": li.description or "",
        "amount": float(li.amount or 0.0),
        "responsible_party": li.responsible_party,
        "notes": li.notes,
        "is_manual": is_manual,
    }
    if li.events:
        data["event_id"] = li.events[0].id
    return data


def _pg_serialize_user(user: Any) -> Dict[str, Any]:
    """Convert User ORM to dict"""
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "password_hash": user.password_hash,
    }


def _pg_serialize_event(event: Any) -> Dict[str, Any]:
    """Convert Event ORM to dict"""
    amount = float(event.total_amount) if event.total_amount else 0.0
    line_item_ids = [li.id for li in event.line_items]
    tag_names = [tag.name for tag in event.tags] if event.tags else []

    return {
        "id": event.id,
        "date": _serialize_datetime(event.date),
        "name": event.description or "",
        "category": event.category.name if event.category else "Unknown",
        "amount": amount,
        "line_items": line_item_ids,
        "tags": tag_names,
        "is_duplicate_transaction": event.is_duplicate or False,
    }


def get_all_line_items(filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get line items from PostgreSQL"""
    from models.database import SessionLocal
    from models.sql_models import Event, LineItem, PaymentMethod

    with SessionLocal.begin() as db:
        query = db.query(LineItem).options(
            joinedload(LineItem.payment_method),
            joinedload(LineItem.events),
            joinedload(LineItem.transaction),
        )

        if filters:
            # Handle id: {$in: [...]} pattern (used in event creation)
            if "id" in filters:
                id_filter = filters["id"]
                if isinstance(id_filter, dict) and "$in" in id_filter:
                    ids = [str(id) for id in id_filter["$in"]]
                    query = query.filter(LineItem.id.in_(ids))

            if "payment_method" in filters and filters["payment_method"] not in [
                "All",
                None,
            ]:
                query = query.join(LineItem.payment_method).filter(PaymentMethod.name == filters["payment_method"])

            if "event_id" in filters:
                if isinstance(filters["event_id"], dict) and "$exists" in filters["event_id"]:
                    if not filters["event_id"]["$exists"]:
                        query = query.outerjoin(LineItem.events).filter(Event.id.is_(None))

        query = query.order_by(LineItem.date.desc())
        line_items = query.all()
        return [_pg_serialize_line_item(li) for li in line_items]


def get_line_item_by_id(id: str) -> Optional[Dict[str, Any]]:
    """Get line item from PostgreSQL by ID"""
    from models.database import SessionLocal
    from models.sql_models import LineItem

    with SessionLocal.begin() as db:
        query = db.query(LineItem).options(
            joinedload(LineItem.payment_method),
            joinedload(LineItem.events),
            joinedload(LineItem.transaction),
        )
        line_item = query.filter(LineItem.id == id).first()
        return _pg_serialize_line_item(line_item) if line_item else None


def get_user_by_id(id: str) -> Optional[Dict[str, Any]]:
    """Get user from PostgreSQL by ID"""
    from models.database import SessionLocal
    from models.sql_models import User

    with SessionLocal.begin() as db:
        query = db.query(User)
        user = query.filter(User.id == id).first()
        return _pg_serialize_user(user) if user else None


def get_all_events(filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get events from PostgreSQL"""
    from datetime import datetime

    from models.database import SessionLocal
    from models.sql_models import Event, LineItem

    with SessionLocal.begin() as db:
        # Use subqueryload for one-to-many relationships to avoid duplicate rows
        # joinedload is fine for many-to-one (category)
        query = db.query(Event).options(
            joinedload(Event.category),
            subqueryload(Event.line_items).joinedload(LineItem.payment_method),
            subqueryload(Event.tags),
        )

        if filters and "date" in filters:
            date_filter = filters["date"]
            if isinstance(date_filter, dict):
                from datetime import UTC

                if "$gte" in date_filter:
                    query = query.filter(Event.date >= datetime.fromtimestamp(date_filter["$gte"], UTC))
                if "$lte" in date_filter:
                    query = query.filter(Event.date <= datetime.fromtimestamp(date_filter["$lte"], UTC))

        events = query.order_by(Event.date.desc()).all()
        return [_pg_serialize_event(event) for event in events]


def get_event_by_id(id: str) -> Optional[Dict[str, Any]]:
    """Get event from PostgreSQL by ID"""
    from models.database import SessionLocal
    from models.sql_models import Event, LineItem

    with SessionLocal.begin() as db:
        query = db.query(Event).options(
            joinedload(Event.category),
            joinedload(Event.line_items).joinedload(LineItem.payment_method),
            joinedload(Event.tags),
        )

        event = query.filter(Event.id == id).first()
        return _pg_serialize_event(event) if event else None


def get_transactions(source: str, filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get raw transactions from PostgreSQL by source (venmo_api, splitwise_api, stripe_api, manual)"""
    from models.database import SessionLocal
    from models.sql_models import Transaction

    with SessionLocal.begin() as db:
        query = db.query(Transaction).filter(Transaction.source == source)

        # Apply filters if provided (though typically raw data reads don't use filters)
        if filters:
            # Could add date filters here if needed in the future
            pass

        query = query.order_by(Transaction.transaction_date.desc())
        transactions = query.all()

        return [
            {
                "source_id": txn.source_id,
                **txn.source_data,  # Unpack the JSONB data
            }
            for txn in transactions
        ]


def get_all_bank_accounts(
    filters: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Get bank accounts from PostgreSQL"""
    from models.database import SessionLocal
    from models.sql_models import BankAccount

    with SessionLocal.begin() as db:
        query = db.query(BankAccount)

        if filters and "status" in filters:
            query = query.filter(BankAccount.status == filters["status"])

        accounts = query.all()
        return [
            {
                "id": acc.id,
                "institution_name": acc.institution_name,
                "display_name": acc.display_name,
                "last4": acc.last4,
                "status": acc.status,
                "can_relink": acc.can_relink,
                "currency": acc.currency,
                "latest_balance": float(acc.latest_balance) if acc.latest_balance is not None else None,
                "balance_as_of": acc.balance_as_of,
            }
            for acc in accounts
        ]


def create_manual_transaction(
    transaction_id: str,
    line_item_id: str,
    transaction_date: Any,
    posix_date: float,
    amount: Any,
    description: str,
    payment_method_id: str,
    responsible_party: str,
) -> None:
    """
    Create a manual transaction with its associated line item.

    Manual transactions bypass the bulk upsert pipeline since they don't need
    deduplication logic (there's no external API to re-import from).

    Args:
        transaction_id: Generated txn_xxx ID for the transaction
        line_item_id: Generated li_xxx ID for the line item
        transaction_date: datetime object for the transaction
        posix_date: POSIX timestamp of the transaction date
        amount: Decimal amount for the line item
        description: Transaction description
        payment_method_id: ID of the payment method
        responsible_party: Name of the responsible party
    """
    from models.database import SessionLocal
    from models.sql_models import LineItem, Transaction

    try:
        with SessionLocal.begin() as db:
            transaction = Transaction(
                id=transaction_id,
                source="manual",
                source_id=transaction_id,
                source_data={
                    "date": posix_date,
                    "person": responsible_party,
                    "description": description,
                    "amount": float(amount),
                    "payment_method_id": payment_method_id,
                },
                transaction_date=transaction_date,
            )
            db.add(transaction)

            line_item = LineItem(
                id=line_item_id,
                transaction_id=transaction_id,
                date=transaction_date,
                amount=amount,
                description=description,
                payment_method_id=payment_method_id,
                responsible_party=responsible_party,
            )
            db.add(line_item)
    except Exception as e:
        logger.error(f"Failed to create manual transaction: {e}")
        raise


def delete_manual_transaction(transaction_id: str) -> bool:
    """
    Delete a manual transaction and its associated line items.

    Args:
        transaction_id: The transaction ID to delete

    Returns:
        True if deleted, False if not found

    Raises:
        ValueError: If the transaction's line item is assigned to an event
    """
    from models.database import SessionLocal
    from models.sql_models import EventLineItem, LineItem, Transaction

    try:
        with SessionLocal.begin() as db:
            transaction = (
                db.query(Transaction).filter(Transaction.id == transaction_id, Transaction.source == "manual").first()
            )

            if not transaction:
                return False

            line_item = db.query(LineItem).filter(LineItem.transaction_id == transaction.id).first()

            if line_item:
                is_assigned = db.query(EventLineItem).filter(EventLineItem.line_item_id == line_item.id).first()
                if is_assigned:
                    raise ValueError("Cannot delete transaction with line item assigned to an event")

            # line item is deleted by cascade
            db.delete(transaction)
            return True
    except Exception as e:
        logger.error(f"Failed to delete manual transaction {transaction_id}: {e}")
        raise


def get_payment_method_by_id(payment_method_id: str) -> Optional[Dict[str, Any]]:
    """Get payment method by ID"""
    from models.database import SessionLocal
    from models.sql_models import PaymentMethod

    with SessionLocal.begin() as db:
        pm = db.query(PaymentMethod).filter(PaymentMethod.id == payment_method_id).first()
        if not pm:
            return None
        return {
            "id": pm.id,
            "name": pm.name,
            "type": pm.type,
            "is_active": pm.is_active,
        }
