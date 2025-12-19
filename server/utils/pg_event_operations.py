"""PostgreSQL operations for events - extracted from resources/event.py for reuse in tests"""

import logging
from datetime import UTC, datetime
from typing import Any, Dict

from models.sql_models import Category, Event, EventLineItem, EventTag, LineItem, Tag
from utils.id_generator import generate_id

logger = logging.getLogger(__name__)


def upsert_event_to_postgresql(event_dict: Dict[str, Any], db_session) -> str:
    """
    Write event to PostgreSQL with all relationships.

    Args:
        event_dict: Event dictionary with fields: id, name/description,
            category, date, tags, line_items, is_duplicate_transaction
        db_session: SQLAlchemy session

    Returns:
        PostgreSQL event ID

    Raises:
        ValueError: If category is missing or not found
        Exception: Any database errors (caller must handle rollback)
    """
    # Generate PostgreSQL ID
    pg_event_id = generate_id("event")

    # Look up category by name - REQUIRED, raise if missing
    category_name = event_dict.get("category")
    if not category_name:
        raise ValueError(f"Event {event_dict.get('id')} has no category - cannot write to PostgreSQL")

    category = db_session.query(Category).filter(Category.name == category_name).first()
    if not category:
        raise ValueError(f"Category '{category_name}' not found in PostgreSQL - cannot write event")

    # Convert date to datetime
    event_date = datetime.fromtimestamp(event_dict["date"], UTC)

    # Check if event already exists by ID (upsert logic)
    existing_event = db_session.query(Event).filter(Event.id == event_dict["id"]).first()

    if existing_event:
        # Update existing event
        existing_event.date = event_date
        existing_event.description = event_dict.get("name", event_dict.get("description", ""))
        existing_event.category_id = category.id
        existing_event.is_duplicate = event_dict.get("is_duplicate_transaction", False)
        existing_event.updated_at = datetime.now(UTC)
        event = existing_event
        pg_event_id = existing_event.id

        # Remove existing junctions (will be recreated below)
        db_session.query(EventLineItem).filter(EventLineItem.event_id == pg_event_id).delete()
        db_session.query(EventTag).filter(EventTag.event_id == pg_event_id).delete()
    else:
        # Create new Event record
        event = Event(
            id=event_dict["id"] if event_dict.get("id") and event_dict["id"].startswith("evt_") else pg_event_id,
            date=event_date,
            description=event_dict.get("name", event_dict.get("description", "")),  # Handle both fields
            category_id=category.id,
            is_duplicate=event_dict.get("is_duplicate_transaction", False),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(event)
        db_session.flush()  # Get the event ID
        pg_event_id = event.id

    # Create EventLineItem junctions
    for line_item_id in event_dict.get("line_items", []):
        pg_line_item = db_session.query(LineItem).filter(LineItem.id == str(line_item_id)).first()

        if pg_line_item:
            event_line_item = EventLineItem(
                id=generate_id("eli"),
                event_id=pg_event_id,
                line_item_id=pg_line_item.id,
                created_at=datetime.now(UTC),
            )
            db_session.add(event_line_item)
        else:
            logger.warning(f"Line item {line_item_id} not in PostgreSQL yet - skipping junction")

    # Create EventTag junctions
    for tag_name in event_dict.get("tags", []):
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

        event_tag = EventTag(
            id=generate_id("etag"),
            event_id=pg_event_id,
            tag_id=tag.id,
            created_at=datetime.now(UTC),
        )
        db_session.add(event_tag)

    return pg_event_id
