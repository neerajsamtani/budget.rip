from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import joinedload, subqueryload

from serializers import serialize_datetime, serialize_event, serialize_line_item, serialize_transaction_source, serialize_user


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


def get_all_line_items(
    ids: Optional[List[str]] = None,
    payment_method: Optional[str] = None,
    only_unreviewed: bool = False,
    limit: Optional[int] = None,
    offset: int = 0,
    event_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get line items from PostgreSQL"""
    from models.database import SessionLocal
    from models.sql_models import EventLineItem, LineItem, PaymentMethod, Transaction

    with SessionLocal.begin() as db:
        event_id_col = func.min(EventLineItem.event_id).label("event_id")
        query = (
            db.query(
                LineItem.id,
                LineItem.transaction_id,
                LineItem.date,
                LineItem.payment_method_id,
                PaymentMethod.name.label("payment_method"),
                LineItem.description,
                LineItem.amount,
                LineItem.responsible_party,
                LineItem.notes,
                Transaction.source.label("transaction_source"),
                event_id_col,
            )
            .join(PaymentMethod, LineItem.payment_method_id == PaymentMethod.id)
            .join(Transaction, LineItem.transaction_id == Transaction.id)
            .outerjoin(EventLineItem, EventLineItem.line_item_id == LineItem.id)
        )

        if ids is not None:
            query = query.filter(LineItem.id.in_(ids))
        if payment_method and payment_method != "All":
            query = query.filter(PaymentMethod.name == payment_method)
        if event_id:
            query = query.filter(EventLineItem.event_id == event_id)
        if only_unreviewed:
            query = query.filter(EventLineItem.event_id.is_(None))

        query = query.group_by(
            LineItem.id,
            LineItem.transaction_id,
            LineItem.date,
            LineItem.payment_method_id,
            PaymentMethod.name,
            LineItem.description,
            LineItem.amount,
            LineItem.responsible_party,
            LineItem.notes,
            Transaction.source,
        )
        query = query.order_by(func.date(LineItem.date).desc(), LineItem.description.asc(), LineItem.id.asc())

        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return [
            {
                "id": row.id,
                "transaction_id": row.transaction_id,
                "date": serialize_datetime(row.date),
                "payment_method_id": row.payment_method_id,
                "payment_method": row.payment_method or "Unknown",
                "source": row.transaction_source or "unknown",
                "source_label": serialize_transaction_source(row.transaction_source),
                "description": row.description or "",
                "amount": float(row.amount or 0.0),
                "responsible_party": row.responsible_party,
                "notes": row.notes,
                "is_manual": row.transaction_source == "manual",
                **({"event_id": row.event_id} if row.event_id else {}),
            }
            for row in query.all()
        ]


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
        return serialize_line_item(line_item) if line_item else None


def get_user_by_id(id: str) -> Optional[Dict[str, Any]]:
    """Get user from PostgreSQL by ID"""
    from models.database import SessionLocal
    from models.sql_models import User

    with SessionLocal.begin() as db:
        query = db.query(User)
        user = query.filter(User.id == id).first()
        return serialize_user(user) if user else None


def get_all_events(
    filters: Optional[Dict[str, Any]],
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Get events from PostgreSQL"""
    from datetime import UTC, datetime

    from models.database import SessionLocal
    from models.sql_models import Category, Event, EventLineItem, EventTag, LineItem, Tag

    with SessionLocal.begin() as db:
        query = db.query(
            Event.id,
            Event.date,
            Event.description,
            Event.is_duplicate,
            Category.name.label("category"),
        ).join(Category, Event.category_id == Category.id)

        if filters and "date" in filters:
            date_filter = filters["date"]
            if isinstance(date_filter, dict):
                if "$gte" in date_filter:
                    query = query.filter(Event.date >= datetime.fromtimestamp(date_filter["$gte"], UTC))
                if "$lte" in date_filter:
                    query = query.filter(Event.date <= datetime.fromtimestamp(date_filter["$lte"], UTC))

        query = query.order_by(Event.date.desc())
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        events = query.all()
        event_ids = [event.id for event in events]
        if not event_ids:
            return []

        amount_rows = (
            db.query(
                EventLineItem.event_id,
                func.sum(LineItem.amount).label("total_amount"),
                func.min(LineItem.amount).label("duplicate_amount"),
            )
            .join(LineItem, EventLineItem.line_item_id == LineItem.id)
            .filter(EventLineItem.event_id.in_(event_ids))
            .group_by(EventLineItem.event_id)
            .all()
        )
        amounts = {
            row.event_id: {
                "total": float(row.total_amount or 0.0),
                "duplicate": float(row.duplicate_amount or 0.0),
            }
            for row in amount_rows
        }

        line_item_rows = (
            db.query(EventLineItem.event_id, EventLineItem.line_item_id)
            .filter(EventLineItem.event_id.in_(event_ids))
            .order_by(EventLineItem.created_at.asc(), EventLineItem.line_item_id.asc())
            .all()
        )
        line_items_by_event: Dict[str, List[str]] = {event_id: [] for event_id in event_ids}
        for row in line_item_rows:
            line_items_by_event[row.event_id].append(row.line_item_id)

        tag_rows = (
            db.query(EventTag.event_id, Tag.name)
            .join(Tag, EventTag.tag_id == Tag.id)
            .filter(EventTag.event_id.in_(event_ids))
            .order_by(Tag.name.asc())
            .all()
        )
        tags_by_event: Dict[str, List[str]] = {event_id: [] for event_id in event_ids}
        for row in tag_rows:
            tags_by_event[row.event_id].append(row.name)

        return [
            {
                "id": event.id,
                "date": serialize_datetime(event.date),
                "name": event.description or "",
                "category": event.category or "Unknown",
                "amount": amounts.get(event.id, {}).get(
                    "duplicate" if event.is_duplicate else "total",
                    0.0,
                ),
                "line_items": line_items_by_event[event.id],
                "tags": tags_by_event[event.id],
                "is_duplicate_transaction": event.is_duplicate or False,
            }
            for event in events
        ]


def get_line_items_for_event(event_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get line items for an event without loading the full event graph."""
    from models.database import SessionLocal
    from models.sql_models import Event

    with SessionLocal.begin() as db:
        event_exists = db.query(Event.id).filter(Event.id == event_id).first()
        if not event_exists:
            return None

    return get_all_line_items(event_id=event_id)


def get_event_by_id(id: str) -> Optional[Dict[str, Any]]:
    """Get event from PostgreSQL by ID"""
    from models.database import SessionLocal
    from models.sql_models import Event, LineItem

    with SessionLocal.begin() as db:
        query = db.query(Event).options(
            joinedload(Event.category),
            subqueryload(Event.line_items).joinedload(LineItem.payment_method),
            subqueryload(Event.tags),
        )

        event = query.filter(Event.id == id).first()
        return serialize_event(event) if event else None


def get_transactions(source: str, filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get raw transactions from PostgreSQL by source (venmo_api, splitwise_api, stripe_api, manual)"""
    from models.database import SessionLocal
    from models.sql_models import Transaction

    with SessionLocal.begin() as db:
        query = db.query(Transaction).filter(Transaction.source == source)

        if filters:
            pass

        query = query.order_by(Transaction.transaction_date.desc())
        transactions = query.all()

        return [
            {
                "source_id": txn.source_id,
                **txn.source_data,
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
