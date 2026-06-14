from typing import Any, Dict, List, Optional

from sqlalchemy.orm import joinedload, subqueryload

from serializers import serialize_event, serialize_line_item, serialize_user


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
) -> List[Dict[str, Any]]:
    """Get line items from PostgreSQL.

    NOTE: Line items are not yet user-scoped. They have no direct user_id FK and
    their only association with a user is transitively, through an event's
    category — but unreviewed line items have no event by definition. Filtering
    here would require a schema change (a user_id FK on LineItem, populated from
    the owning integration). Tracked as the follow-up to plan 023; until then
    this is a single-user assumption.
    """
    from models.database import SessionLocal
    from models.sql_models import Event, LineItem, PaymentMethod

    with SessionLocal.begin() as db:
        query = db.query(LineItem).options(
            joinedload(LineItem.payment_method),
            joinedload(LineItem.events),
            joinedload(LineItem.transaction),
        )

        if ids is not None:
            query = query.filter(LineItem.id.in_(ids))
        if payment_method and payment_method != "All":
            query = query.join(LineItem.payment_method).filter(PaymentMethod.name == payment_method)
        if only_unreviewed:
            query = query.outerjoin(LineItem.events).filter(Event.id.is_(None))

        query = query.order_by(LineItem.date.desc())
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        line_items = query.all()
        return [serialize_line_item(li) for li in line_items]


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
    user_id: str,
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Get events from PostgreSQL, scoped to the given user.

    Isolation is enforced explicitly via the Event -> Category -> user_id join
    rather than relying on the implicit category ownership chain.
    """
    from datetime import datetime

    from models.database import SessionLocal
    from models.sql_models import Category, Event, LineItem

    with SessionLocal.begin() as db:
        # Use subqueryload for one-to-many relationships to avoid duplicate rows
        # joinedload is fine for many-to-one (category)
        query = (
            db.query(Event)
            .join(Category, Event.category_id == Category.id)
            .filter(Category.user_id == user_id)
            .options(
                joinedload(Event.category),
                subqueryload(Event.line_items).joinedload(LineItem.payment_method),
                subqueryload(Event.tags),
            )
        )

        if filters and "date" in filters:
            date_filter = filters["date"]
            if isinstance(date_filter, dict):
                from datetime import UTC

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
        return [serialize_event(event) for event in events]


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
