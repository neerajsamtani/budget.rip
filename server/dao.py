import logging
from datetime import timezone as tz
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import joinedload, subqueryload

from helpers import to_dict

logger = logging.getLogger(__name__)

venmo_raw_data_collection: str = "venmo_raw_data"
splitwise_raw_data_collection: str = "splitwise_raw_data"
cash_raw_data_collection: str = "cash_raw_data"
stripe_raw_transaction_data_collection: str = "stripe_raw_transaction_data"
stripe_raw_account_data_collection: str = "stripe_raw_account_data"
line_items_collection: str = "line_items"
events_collection: str = "events"
bank_accounts_collection: str = "accounts"
users_collection: str = "users"
test_collection: str = "test_data"


def get_all_data(cur_collection_str: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Get all data from PostgreSQL for the specified collection"""
    if cur_collection_str == line_items_collection:
        return _pg_get_all_line_items(filters)
    elif cur_collection_str == events_collection:
        return _pg_get_all_events(filters)
    elif cur_collection_str == bank_accounts_collection:
        return _pg_get_all_bank_accounts(filters)
    elif cur_collection_str == venmo_raw_data_collection:
        return _pg_get_transactions("venmo", filters)
    elif cur_collection_str == splitwise_raw_data_collection:
        return _pg_get_transactions("splitwise", filters)
    elif cur_collection_str == stripe_raw_transaction_data_collection:
        return _pg_get_transactions("stripe", filters)
    elif cur_collection_str == cash_raw_data_collection:
        return _pg_get_transactions("cash", filters)
    else:
        raise NotImplementedError(f"Collection {cur_collection_str} not supported for get_all_data")


def get_item_by_id(cur_collection_str: str, id: Union[str, int]) -> Optional[Dict[str, Any]]:
    """Get item by ID from PostgreSQL for the specified collection"""
    if cur_collection_str == line_items_collection:
        return _pg_get_line_item_by_id(str(id))
    elif cur_collection_str == events_collection:
        return _pg_get_event_by_id(str(id))
    elif cur_collection_str == users_collection:
        return _pg_get_user_by_id(str(id))
    else:
        raise NotImplementedError(f"Collection {cur_collection_str} not supported for get_item_by_id")


def remove_event_from_line_item(line_item_id: Union[str, int]) -> None:
    """
    Remove event association from a line item by its ID (PostgreSQL only).

    Args:
        line_item_id: The ID of the line item (can be string, int, or ObjectId)
    """
    from models.database import SessionLocal
    from models.sql_models import EventLineItem, LineItem

    db = SessionLocal()
    try:
        # Find the line item by ID
        line_item = db.query(LineItem).filter(LineItem.id == str(line_item_id)).first()

        if line_item:
            # Delete all EventLineItem junctions for this line item
            db.query(EventLineItem).filter(EventLineItem.line_item_id == line_item.id).delete()
            db.commit()
        else:
            logger.warning(f"Could not find line item with ID {line_item_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to remove event from line item: {e}")
        raise
    finally:
        db.close()


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    logger.debug("Reading user by email from PostgreSQL")
    return _pg_get_user_by_email(email)


def upsert(cur_collection_str: str, item: Any) -> None:
    item_dict: Dict[str, Any] = to_dict(item)
    upsert_with_id(cur_collection_str, item_dict, item_dict["id"])


def upsert_with_id(cur_collection_str: str, item: Dict[str, Any], id: Union[str, int]) -> None:
    """Upsert item to PostgreSQL for migrated collections"""
    from models.database import SessionLocal

    db = SessionLocal()
    try:
        # PostgreSQL write for transaction collections
        if cur_collection_str in [
            venmo_raw_data_collection,
            splitwise_raw_data_collection,
            stripe_raw_transaction_data_collection,
            cash_raw_data_collection,
        ]:
            from utils.pg_bulk_ops import _bulk_upsert_transactions

            source_map = {
                venmo_raw_data_collection: "venmo",
                splitwise_raw_data_collection: "splitwise",
                stripe_raw_transaction_data_collection: "stripe",
                cash_raw_data_collection: "cash",
            }
            source = source_map[cur_collection_str]
            _bulk_upsert_transactions(db, [item], source=source)

        elif cur_collection_str == events_collection:
            from utils.pg_event_operations import upsert_event_to_postgresql

            upsert_event_to_postgresql(item, db)

        elif cur_collection_str == bank_accounts_collection:
            from utils.pg_bulk_ops import _bulk_upsert_bank_accounts

            _bulk_upsert_bank_accounts(db, [item])

        elif cur_collection_str == line_items_collection:
            from utils.pg_bulk_ops import _bulk_upsert_line_items

            # Derive source from payment_method if not explicitly provided
            payment_method = item.get("payment_method", "cash").lower()
            source_map = {
                "venmo": "venmo",
                "splitwise": "splitwise",
                "credit card": "stripe",
                "debit card": "stripe",
                "cash": "cash",
            }
            source = source_map.get(payment_method, "cash")
            _bulk_upsert_line_items(db, [item], source=source)

        else:
            raise NotImplementedError(f"Collection {cur_collection_str} not supported for upsert_with_id")

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to upsert item to {cur_collection_str}: {e}")
        raise
    finally:
        db.close()


def get_categorized_data() -> List[Dict[str, Any]]:
    """Group totalExpense by month, year, and category"""
    logger.debug("Reading categorized data from PostgreSQL")
    return _pg_get_categorized_data()


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
    data = {
        "id": li.id,
        "date": _serialize_datetime(li.date),
        "payment_method": li.payment_method.name if li.payment_method else "Unknown",
        "description": li.description or "",
        "amount": float(li.amount or 0.0),
        "responsible_party": li.responsible_party,
        "notes": li.notes,
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


def _pg_get_all_line_items(filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get line items from PostgreSQL"""
    from models.database import SessionLocal
    from models.sql_models import Event, LineItem, PaymentMethod

    db_session = SessionLocal()
    try:
        query = db_session.query(LineItem).options(joinedload(LineItem.payment_method), joinedload(LineItem.events))

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
    finally:
        db_session.close()


def _pg_get_line_item_by_id(id: str) -> Optional[Dict[str, Any]]:
    """Get line item from PostgreSQL by ID"""
    from models.database import SessionLocal
    from models.sql_models import LineItem

    db_session = SessionLocal()
    try:
        query = db_session.query(LineItem).options(joinedload(LineItem.payment_method), joinedload(LineItem.events))
        line_item = query.filter(LineItem.id == id).first()
        return _pg_serialize_line_item(line_item) if line_item else None
    finally:
        db_session.close()


def _pg_get_user_by_id(id: str) -> Optional[Dict[str, Any]]:
    """Get user from PostgreSQL by ID"""
    from models.database import SessionLocal
    from models.sql_models import User

    db_session = SessionLocal()
    try:
        query = db_session.query(User)
        user = query.filter(User.id == id).first()
        return _pg_serialize_user(user) if user else None
    finally:
        db_session.close()


def _pg_get_all_events(filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get events from PostgreSQL"""
    from datetime import datetime

    from models.database import SessionLocal
    from models.sql_models import Event, LineItem

    db_session = SessionLocal()
    try:
        # Use subqueryload for one-to-many relationships to avoid duplicate rows
        # joinedload is fine for many-to-one (category)
        query = db_session.query(Event).options(
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
    finally:
        db_session.close()


def _pg_get_event_by_id(id: str) -> Optional[Dict[str, Any]]:
    """Get event from PostgreSQL by ID"""
    from models.database import SessionLocal
    from models.sql_models import Event, LineItem

    db_session = SessionLocal()
    try:
        query = db_session.query(Event).options(
            joinedload(Event.category),
            joinedload(Event.line_items).joinedload(LineItem.payment_method),
            joinedload(Event.tags),
        )

        event = query.filter(Event.id == id).first()
        return _pg_serialize_event(event) if event else None
    finally:
        db_session.close()


def _pg_get_line_items_for_event(event_id: str) -> List[Dict[str, Any]]:
    """Get line items for event from PostgreSQL"""
    from models.database import SessionLocal
    from models.sql_models import Event, EventLineItem, LineItem

    db_session = SessionLocal()
    try:
        pg_event = db_session.query(Event).filter(Event.id == event_id).first()

        if not pg_event:
            return []

        line_items = (
            db_session.query(LineItem)
            .join(EventLineItem, LineItem.id == EventLineItem.line_item_id)
            .filter(EventLineItem.event_id == pg_event.id)
            .options(joinedload(LineItem.payment_method), joinedload(LineItem.events))
            .all()
        )

        return [_pg_serialize_line_item(li) for li in line_items]
    finally:
        db_session.close()


def _pg_get_categorized_data() -> List[Dict[str, Any]]:
    """Get monthly breakdown from PostgreSQL"""
    from sqlalchemy import extract, func

    from models.database import SessionLocal
    from models.sql_models import Category, Event, LineItem

    db_session = SessionLocal()
    try:
        results = (
            db_session.query(
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
    finally:
        db_session.close()


def _pg_get_transactions(source: str, filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get raw transactions from PostgreSQL by source (venmo, splitwise, stripe, cash)"""
    from models.database import SessionLocal
    from models.sql_models import Transaction

    db_session = SessionLocal()
    try:
        query = db_session.query(Transaction).filter(Transaction.source == source)

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
    finally:
        db_session.close()


def _pg_get_all_bank_accounts(
    filters: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Get bank accounts from PostgreSQL"""
    from models.database import SessionLocal
    from models.sql_models import BankAccount

    db_session = SessionLocal()
    try:
        query = db_session.query(BankAccount)

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
    finally:
        db_session.close()


def _pg_get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user from PostgreSQL by email"""
    from models.database import SessionLocal
    from models.sql_models import User

    db_session = SessionLocal()
    try:
        user = db_session.query(User).filter(User.email == email).first()
        if not user:
            return None
        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "password_hash": user.password_hash,
        }
    finally:
        db_session.close()
