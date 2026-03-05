"""
Test helper utilities for creating test data in the database.

These factories reduce boilerplate in tests by handling foreign key relationships.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from models.sql_models import (
    Category,
    Event,
    EventLineItem,
    LineItem,
    PaymentMethod,
    Transaction,
    User,
)
from utils.id_generator import generate_id


def setup_test_line_item(db_session, item_data: Dict[str, Any]) -> LineItem:
    """
    Create a line item in the database.

    Args:
        db_session: Database session
        item_data: Dict with keys: id, date, payment_method, description,
                   responsible_party, amount, and optionally event_id, notes

    Returns:
        LineItem object
    """
    payment_method = db_session.query(PaymentMethod).filter(PaymentMethod.name == item_data["payment_method"]).first()

    if not payment_method:
        raise ValueError(f"Payment method '{item_data['payment_method']}' not found. Ensure seed_base_data fixture is used.")

    # Create transaction (required FK for line item)
    transaction = Transaction(
        id=generate_id("txn"),
        source="manual",
        source_id=item_data["id"],
        transaction_date=datetime.fromtimestamp(item_data["date"], UTC),
        source_data={},
        created_at=datetime.now(UTC),
    )
    db_session.add(transaction)
    db_session.flush()

    # Create line item
    line_item = LineItem(
        id=generate_id("li"),
        transaction_id=transaction.id,
        date=datetime.fromtimestamp(item_data["date"], UTC),
        description=item_data["description"],
        amount=item_data["amount"],
        responsible_party=item_data["responsible_party"],
        payment_method_id=payment_method.id,
        notes=item_data.get("notes"),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(line_item)
    db_session.flush()

    return line_item


def setup_test_event(
    db_session,
    event_data: Dict[str, Any],
    line_items: Optional[List[LineItem]] = None,
) -> Event:
    """
    Create an event in the database.

    Args:
        db_session: Database session
        event_data: Dict with keys: id, date, description, category,
                    and optionally is_duplicate, tags
        line_items: List of LineItem objects to associate with event

    Returns:
        Event object
    """
    category = db_session.query(Category).filter(Category.name == event_data["category"]).first()

    if not category:
        raise ValueError(f"Category '{event_data['category']}' not found. Ensure seed_base_data fixture is used.")

    event = Event(
        id=generate_id("event"),
        date=datetime.fromtimestamp(event_data["date"], UTC),
        description=event_data.get("description", ""),
        category_id=category.id,
        is_duplicate=event_data.get("is_duplicate", False),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(event)
    db_session.flush()

    # Link line items if provided
    if line_items:
        for line_item in line_items:
            event_line_item = EventLineItem(
                id=generate_id("eli"),
                event_id=event.id,
                line_item_id=line_item.id,
            )
            db_session.add(event_line_item)

    # Handle tags if present
    if "tags" in event_data and event_data["tags"]:
        from models.sql_models import EventTag, Tag

        for tag_name in event_data["tags"]:
            tag = db_session.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(
                    id=generate_id("tag"),
                    name=tag_name,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                db_session.add(tag)
                db_session.flush()

            event_tag = EventTag(id=generate_id("et"), event_id=event.id, tag_id=tag.id)
            db_session.add(event_tag)

    db_session.flush()
    return event


def setup_test_user(db_session, user_data: Dict[str, Any]) -> User:
    """
    Create a user in the database.

    Args:
        db_session: Database session
        user_data: Dict with keys: id, email, first_name, last_name, password_hash

    Returns:
        User object
    """
    user = User(
        id=generate_id("user"),
        email=user_data["email"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        password_hash=user_data["password_hash"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(user)
    db_session.flush()

    return user


def setup_test_line_item_with_event(db_session, item_data: Dict[str, Any], event_id: str) -> LineItem:
    """
    Convenience helper to create a line item and link it to an existing event.

    Args:
        db_session: Database session
        item_data: Line item data (must include 'id', 'date', etc.)
        event_id: ID of existing event

    Returns:
        LineItem object
    """
    # Create line item
    line_item = setup_test_line_item(db_session, item_data)

    # Find event
    event = db_session.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise ValueError(f"Event {event_id} not found")

    # Create junction
    event_line_item = EventLineItem(
        id=generate_id("eli"),
        event_id=event.id,
        line_item_id=line_item.id,
    )
    db_session.add(event_line_item)
    db_session.flush()

    return line_item
