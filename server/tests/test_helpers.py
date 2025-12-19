"""
Test helper utilities for creating test data in PostgreSQL.

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


def setup_test_line_item(pg_session, item_data: Dict[str, Any], mongo_only: bool = False) -> Optional[LineItem]:
    """
    Create a line item in PostgreSQL.

    Args:
        pg_session: PostgreSQL session
        item_data: Dict with keys: id, date, payment_method, description,
                   responsible_party, amount, and optionally event_id, notes
        mongo_only: Deprecated parameter, ignored (kept for backward compatibility)

    Returns:
        PostgreSQL LineItem object
    """
    # Write to PostgreSQL
    payment_method = pg_session.query(PaymentMethod).filter(PaymentMethod.name == item_data["payment_method"]).first()

    if not payment_method:
        raise ValueError(
            f"Payment method '{item_data['payment_method']}' not found. Ensure seed_postgresql_base_data fixture is used."
        )

    # Create transaction (required FK for line item)
    pg_transaction = Transaction(
        id=generate_id("txn"),
        source="manual",
        source_id=item_data["id"],
        transaction_date=datetime.fromtimestamp(item_data["date"], UTC),
        source_data={},
        created_at=datetime.now(UTC),
    )
    pg_session.add(pg_transaction)
    pg_session.flush()

    # Create line item
    pg_line_item = LineItem(
        id=generate_id("li"),
        transaction_id=pg_transaction.id,
        mongo_id=item_data["id"],
        date=datetime.fromtimestamp(item_data["date"], UTC),
        description=item_data["description"],
        amount=item_data["amount"],
        responsible_party=item_data["responsible_party"],
        payment_method_id=payment_method.id,
        notes=item_data.get("notes"),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    pg_session.add(pg_line_item)
    pg_session.flush()

    return pg_line_item


def setup_test_event(
    pg_session,
    event_data: Dict[str, Any],
    line_items: Optional[List[LineItem]] = None,
    mongo_only: bool = False,
) -> Optional[Event]:
    """
    Create an event in PostgreSQL.

    Args:
        pg_session: PostgreSQL session
        event_data: Dict with keys: id, date, description, category,
                    and optionally is_duplicate, tags
        line_items: List of PostgreSQL LineItem objects to associate with event
        mongo_only: Deprecated parameter, ignored (kept for backward compatibility)

    Returns:
        PostgreSQL Event object
    """
    # Write to PostgreSQL
    category = pg_session.query(Category).filter(Category.name == event_data["category"]).first()

    if not category:
        raise ValueError(f"Category '{event_data['category']}' not found. Ensure seed_postgresql_base_data fixture is used.")

    pg_event = Event(
        id=generate_id("event"),
        mongo_id=event_data["id"],
        date=datetime.fromtimestamp(event_data["date"], UTC),
        description=event_data.get("description", ""),
        category_id=category.id,
        is_duplicate=event_data.get("is_duplicate", False),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    pg_session.add(pg_event)
    pg_session.flush()

    # Link line items if provided
    if line_items:
        for pg_line_item in line_items:
            event_line_item = EventLineItem(
                id=generate_id("eli"),
                event_id=pg_event.id,
                line_item_id=pg_line_item.id,
            )
            pg_session.add(event_line_item)

    # Handle tags if present
    if "tags" in event_data and event_data["tags"]:
        from models.sql_models import EventTag, Tag

        for tag_name in event_data["tags"]:
            tag = pg_session.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(
                    id=generate_id("tag"),
                    name=tag_name,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                pg_session.add(tag)
                pg_session.flush()

            event_tag = EventTag(id=generate_id("et"), event_id=pg_event.id, tag_id=tag.id)
            pg_session.add(event_tag)

    pg_session.flush()
    return pg_event


def setup_test_user(pg_session, user_data: Dict[str, Any], mongo_only: bool = False) -> Optional[User]:
    """
    Create a user in PostgreSQL.

    Args:
        pg_session: PostgreSQL session
        user_data: Dict with keys: id, email, first_name, last_name, password_hash
        mongo_only: Deprecated parameter, ignored (kept for backward compatibility)

    Returns:
        PostgreSQL User object
    """
    # Write to PostgreSQL
    pg_user = User(
        id=generate_id("user"),
        mongo_id=user_data["id"],
        email=user_data["email"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        password_hash=user_data["password_hash"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    pg_session.add(pg_user)
    pg_session.flush()

    return pg_user


def setup_test_line_item_with_event(pg_session, item_data: Dict[str, Any], event_id: str) -> LineItem:
    """
    Convenience helper to create a line item and link it to an existing event.

    Args:
        pg_session: PostgreSQL session
        item_data: Line item data (must include 'id', 'date', etc.)
        event_id: ID of existing event (mongo_id or pg id)

    Returns:
        PostgreSQL LineItem object
    """
    # Create line item
    pg_line_item = setup_test_line_item(pg_session, item_data)

    # Find event
    pg_event = pg_session.query(Event).filter(Event.id == event_id).first()
    if not pg_event:
        pg_event = pg_session.query(Event).filter(Event.mongo_id == event_id).first()

    if not pg_event:
        raise ValueError(f"Event {event_id} not found")

    # Create junction
    event_line_item = EventLineItem(
        id=generate_id("eli"),
        event_id=pg_event.id,
        line_item_id=pg_line_item.id,
    )
    pg_session.add(event_line_item)
    pg_session.flush()

    return pg_line_item
