import logging
from decimal import Decimal
from typing import Any, Dict, List, Union

from serializers import serialize_datetime

logger = logging.getLogger(__name__)


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
    except Exception as e:
        logger.error(f"Failed to remove event from line item {line_item_id}: {e}")
        raise


def get_categorized_data() -> List[Dict[str, Any]]:
    """Group totalExpense by month, year, and category.

    Uses SQL subqueries to compute per-event amounts instead of loading all
    LineItem ORM objects, reducing the work from O(events * line_items) to
    O(events). Duplicate events (is_duplicate=True) count only the minimum
    line item amount rather than the sum.
    """
    from collections import defaultdict
    from datetime import timezone as tz

    from sqlalchemy import case, func

    from models.database import SessionLocal
    from models.sql_models import Category, Event, EventLineItem, LineItem

    with SessionLocal.begin() as db:
        # Subquery: total amount per event (sum of all line items)
        total_subq = (
            db.query(
                EventLineItem.event_id,
                func.sum(LineItem.amount).label("total"),
            )
            .join(LineItem, EventLineItem.line_item_id == LineItem.id)
            .group_by(EventLineItem.event_id)
            .subquery()
        )

        # Subquery: minimum line item amount per event (for duplicates)
        min_li_subq = (
            db.query(
                EventLineItem.event_id,
                func.min(LineItem.amount).label("min_amount"),
            )
            .join(LineItem, EventLineItem.line_item_id == LineItem.id)
            .group_by(EventLineItem.event_id)
            .subquery()
        )

        # Main query: events with category and computed amount — no ORM line item loading
        rows = (
            db.query(
                Event.date,
                Category.name.label("category"),
                case(
                    (Event.is_duplicate == True, min_li_subq.c.min_amount),  # noqa: E712
                    else_=total_subq.c.total,
                ).label("amount"),
            )
            .join(Category, Event.category_id == Category.id)
            .outerjoin(total_subq, total_subq.c.event_id == Event.id)
            .outerjoin(min_li_subq, min_li_subq.c.event_id == Event.id)
            .all()
        )

        breakdown: Dict[tuple, Decimal] = defaultdict(Decimal)
        for row in rows:
            if not row.category:
                continue
            utc_date = row.date.astimezone(tz.utc) if row.date.tzinfo else row.date.replace(tzinfo=tz.utc)
            key = (utc_date.year, utc_date.month, row.category)
            breakdown[key] += row.amount if row.amount is not None else Decimal("0")

        return [
            {"year": year, "month": month, "category": category, "totalExpense": float(amount)}
            for (year, month, category), amount in sorted(breakdown.items())
        ]


def get_line_item_amounts(line_item_ids: list[str]) -> List[Dict[str, Any]]:
    """Get only id, date, and amount for the given line items — no relationship loading."""
    from models.database import SessionLocal
    from models.sql_models import LineItem

    with SessionLocal.begin() as db:
        rows = (
            db.query(LineItem.id, LineItem.date, LineItem.amount)
            .filter(LineItem.id.in_([str(id) for id in line_item_ids]))
            .all()
        )
        return [{"id": row.id, "date": serialize_datetime(row.date), "amount": float(row.amount or 0.0)} for row in rows]


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
