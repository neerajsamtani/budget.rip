from datetime import datetime
from datetime import timezone as tz
from typing import Any, Dict, Optional

from models.sql_models import Event, LineItem, User


def serialize_datetime(dt: Optional[datetime]) -> float:
    """Treats naive datetimes from SQLite as UTC to ensure consistent timestamp conversion"""
    if not dt:
        return 0.0

    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz.utc).timestamp()
    else:
        return dt.timestamp()


def serialize_line_item(li: LineItem) -> Dict[str, Any]:
    """Convert LineItem ORM to dict"""
    # Determine if this is a manual transaction based on the source
    is_manual = li.transaction.source == "manual" if li.transaction else False

    data = {
        "id": li.id,
        "date": serialize_datetime(li.date),
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


def serialize_user(user: User) -> Dict[str, Any]:
    """Convert User ORM to dict"""
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "password_hash": user.password_hash,
    }


def serialize_event(event: Event) -> Dict[str, Any]:
    """Convert Event ORM to dict"""
    amount = float(event.total_amount) if event.total_amount else 0.0
    line_item_ids = [li.id for li in event.line_items]
    tag_names = [tag.name for tag in event.tags] if event.tags else []

    return {
        "id": event.id,
        "date": serialize_datetime(event.date),
        "name": event.description or "",
        "category": event.category.name if event.category else "Unknown",
        "amount": amount,
        "line_items": line_item_ids,
        "tags": tag_names,
        "is_duplicate_transaction": event.is_duplicate or False,
    }
