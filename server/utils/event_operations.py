"""Event operations - extracted from resources/event.py for reuse in tests"""

import logging
from datetime import UTC, datetime
from typing import Any, Dict

from models.database import SessionLocal
from models.sql_models import Category, Event, EventLineItem, EventTag, LineItem, Tag
from utils.id_generator import generate_id

logger = logging.getLogger(__name__)


def upsert_event_to_db(event_dict: Dict[str, Any], db_session) -> str:
    """
    Write event to database with all relationships.

    Args:
        event_dict: Event dictionary with fields: id, name/description,
            category, date, tags, line_items, is_duplicate_transaction
        db_session: SQLAlchemy session

    Returns:
        database event ID

    Raises:
        ValueError: If category is missing or not found
        Exception: Any database errors (caller must handle rollback)
    """
    # Generate database ID
    event_id = generate_id("event")

    # Look up category by name - REQUIRED, raise if missing
    category_name = event_dict.get("category")
    if not category_name:
        raise ValueError(f"Event {event_dict.get('id')} has no category - cannot write to database")

    category = db_session.query(Category).filter(Category.name == category_name).first()
    if not category:
        raise ValueError(f"Category '{category_name}' not found in database - cannot write event")

    # Convert date to datetime
    event_date = datetime.fromtimestamp(event_dict["date"], UTC)

    # Check if event already exists by ID (upsert logic)
    existing_event = db_session.query(Event).filter(Event.id == event_dict.get("id")).first() if event_dict.get("id") else None

    if existing_event:
        # Update existing event
        existing_event.date = event_date
        existing_event.description = event_dict.get("name", event_dict.get("description", ""))
        existing_event.category_id = category.id
        existing_event.is_duplicate = event_dict.get("is_duplicate_transaction", False)
        existing_event.updated_at = datetime.now(UTC)
        event = existing_event
        event_id = existing_event.id

        # Remove existing junctions (will be recreated below)
        db_session.query(EventLineItem).filter(EventLineItem.event_id == event_id).delete()
        db_session.query(EventTag).filter(EventTag.event_id == event_id).delete()
    else:
        # Create new Event record
        event = Event(
            id=event_id,
            date=event_date,
            description=event_dict.get("name", event_dict.get("description", "")),  # Handle both fields
            category_id=category.id,
            is_duplicate=event_dict.get("is_duplicate_transaction", False),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(event)
        db_session.flush()  # Get the event ID
        event_id = event.id

    # Create EventLineItem junctions (batch-fetch to avoid N+1)
    line_item_ids = [str(id) for id in event_dict.get("line_items", [])]
    if line_item_ids:
        matched_items = db_session.query(LineItem).filter(LineItem.id.in_(line_item_ids)).all()
        found_ids = {li.id for li in matched_items}
        for li_id in line_item_ids:
            if li_id not in found_ids:
                logger.warning(f"Line item {li_id} not in database yet - skipping junction")
                continue
            event_line_item = EventLineItem(
                id=generate_id("eli"),
                event_id=event_id,
                line_item_id=li_id,
                created_at=datetime.now(UTC),
            )
            db_session.add(event_line_item)

    # Create EventTag junctions (batch-fetch existing tags to avoid N+1)
    tag_names = event_dict.get("tags", [])
    if tag_names:
        existing_tags = db_session.query(Tag).filter(Tag.name.in_(tag_names)).all()
        tag_map = {t.name: t for t in existing_tags}
        for tag_name in tag_names:
            tag = tag_map.get(tag_name)
            if not tag:
                tag = Tag(
                    id=generate_id("tag"),
                    name=tag_name,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                db_session.add(tag)
                db_session.flush()
                tag_map[tag_name] = tag

            event_tag = EventTag(
                id=generate_id("etag"),
                event_id=event_id,
                tag_id=tag.id,
                created_at=datetime.now(UTC),
            )
            db_session.add(event_tag)

    return event_id


def upsert_event(event_dict: Dict[str, Any]) -> str:
    """
    Upsert an event while managing the session lifecycle.
    """
    with SessionLocal.begin() as db_session:
        event_id = upsert_event_to_db(event_dict, db_session)
        return event_id


def delete_event(event_id: str) -> bool:
    """
    Delete an event while managing the session lifecycle.

    Returns:
        True if an event was deleted, False if not found.
    """
    with SessionLocal.begin() as db_session:
        event = db_session.query(Event).filter(Event.id == event_id).first()

        if not event:
            return False

        db_session.delete(event)
        return True
