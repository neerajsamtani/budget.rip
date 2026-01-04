# tests/test_models.py
"""
SQLAlchemy model tests using SQLite in-memory database.

These tests validate model relationships, constraints, and basic behavior.
For PostgreSQL-specific features (JSONB operators, etc.), consider
separate integration tests in CI.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from models.sql_models import (
    Base,
    Category,
    Event,
    EventLineItem,
    LineItem,
    PaymentMethod,
    Transaction,
    User,
)
from utils.id_generator import generate_id


@pytest.fixture
def db_session():
    # Use SQLite in-memory database for testing
    # This provides fast tests without external dependencies
    # SQLite tests basic model logic, relationships, and constraints
    engine = create_engine("sqlite:///:memory:")

    # Enable foreign key constraints in SQLite (disabled by default)
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Drop all tables and recreate for clean test state
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

    # Cleanup after tests
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_user(db_session):
    """Create a test user for use in tests requiring user-scoped data."""
    user = User(
        id=generate_id("user"),
        first_name="Test",
        last_name="User",
        email="test@example.com",
        password_hash="test_hash",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def common_fixtures(db_session, test_user):
    """Create common test objects: category, payment_method, and transaction."""
    category = Category(id=generate_id("cat"), user_id=test_user.id, name="Test Category")
    payment_method = PaymentMethod(id=generate_id("pm"), name="Test Card", type="credit", is_active=True)
    transaction = Transaction(
        id=generate_id("txn"),
        source="manual",
        source_id="test123",
        source_data={},
        transaction_date=datetime.now(UTC),
    )
    db_session.add_all([category, payment_method, transaction])
    db_session.commit()
    return {"category": category, "payment_method": payment_method, "transaction": transaction}


def test_event_can_link_to_line_items_via_junction_table(db_session, common_fixtures):
    category = common_fixtures["category"]
    payment_method = common_fixtures["payment_method"]
    transaction = common_fixtures["transaction"]

    # Create line item
    line_item = LineItem(
        id=generate_id("li"),
        transaction_id=transaction.id,
        date=datetime.now(UTC),
        amount=Decimal("50.00"),
        description="Test purchase",
        payment_method_id=payment_method.id,
    )
    db_session.add(line_item)
    db_session.commit()

    # Create event
    event = Event(
        id=generate_id("evt"),
        date=datetime.now(UTC),
        description="Test Event",
        category_id=category.id,
        is_duplicate=False,
    )
    db_session.add(event)
    db_session.commit()

    # Link line item to event via junction table
    event_line_item = EventLineItem(id=generate_id("eli"), event_id=event.id, line_item_id=line_item.id)
    db_session.add(event_line_item)
    db_session.commit()

    # Refresh to load relationships
    db_session.refresh(event)
    db_session.refresh(line_item)

    # Verify relationship
    assert len(event.line_items) == 1
    assert event.line_items[0].id == line_item.id
    assert len(line_item.events) == 1
    assert line_item.events[0].id == event.id


def test_event_requires_valid_category_id(db_session):
    # Try to create event with invalid category
    with pytest.raises(IntegrityError):
        event = Event(
            id=generate_id("evt"),
            date=datetime.now(UTC),
            description="Test",
            category_id="cat_nonexistent",
            is_duplicate=False,
        )
        db_session.add(event)
        db_session.commit()


def test_event_total_amount_sums_all_linked_line_items(db_session, common_fixtures):
    """Event total_amount property sums all linked line item amounts"""
    category = common_fixtures["category"]
    payment_method = common_fixtures["payment_method"]
    transaction = common_fixtures["transaction"]

    # Create event
    event = Event(
        id=generate_id("evt"),
        date=datetime.now(UTC),
        description="Multi-item event",
        category_id=category.id,
        is_duplicate=False,
    )
    db_session.add(event)
    db_session.commit()

    # Add multiple line items
    amounts = [Decimal("25.00"), Decimal("30.50"), Decimal("15.25")]
    for amount in amounts:
        line_item = LineItem(
            id=generate_id("li"),
            transaction_id=transaction.id,
            date=datetime.now(UTC),
            amount=amount,
            description="Test item",
            payment_method_id=payment_method.id,
        )
        db_session.add(line_item)
        db_session.commit()

        # Link to event
        event_line_item = EventLineItem(id=generate_id("eli"), event_id=event.id, line_item_id=line_item.id)
        db_session.add(event_line_item)

    db_session.commit()
    db_session.refresh(event)

    # Verify total
    expected_total = sum(amounts)
    assert event.total_amount == expected_total


def test_duplicate_event_uses_first_line_item_amount_only(db_session, common_fixtures):
    """Duplicate event uses only the first line item amount"""
    category = common_fixtures["category"]
    payment_method = common_fixtures["payment_method"]
    transaction = common_fixtures["transaction"]

    # Create duplicate event
    event = Event(
        id=generate_id("evt"),
        date=datetime.now(UTC),
        description="Duplicate transaction",
        category_id=category.id,
        is_duplicate=True,  # Mark as duplicate
    )
    db_session.add(event)
    db_session.commit()

    # Add two line items with different amounts
    amounts = [Decimal("100.00"), Decimal("100.00")]
    for amount in amounts:
        line_item = LineItem(
            id=generate_id("li"),
            transaction_id=transaction.id,
            date=datetime.now(UTC),
            amount=amount,
            description="Duplicate charge",
            payment_method_id=payment_method.id,
        )
        db_session.add(line_item)
        db_session.commit()

        event_line_item = EventLineItem(id=generate_id("eli"), event_id=event.id, line_item_id=line_item.id)
        db_session.add(event_line_item)

    db_session.commit()
    db_session.refresh(event)

    # With is_duplicate=True, should use first item only
    assert event.total_amount == Decimal("100.00")
    # Not the sum of both (200.00)
    assert event.total_amount != sum(amounts)


def test_deleting_event_cascades_to_junction_table(db_session, common_fixtures):
    """Deleting an event cascades to event_line_items but preserves line items"""
    category = common_fixtures["category"]
    payment_method = common_fixtures["payment_method"]
    transaction = common_fixtures["transaction"]

    # Create event and line item
    event = Event(
        id=generate_id("evt"),
        date=datetime.now(UTC),
        description="Test Event",
        category_id=category.id,
        is_duplicate=False,
    )
    line_item = LineItem(
        id=generate_id("li"),
        transaction_id=transaction.id,
        date=datetime.now(UTC),
        amount=Decimal("50.00"),
        description="Test item",
        payment_method_id=payment_method.id,
    )
    db_session.add_all([event, line_item])
    db_session.commit()

    # Link them
    event_line_item = EventLineItem(id=generate_id("eli"), event_id=event.id, line_item_id=line_item.id)
    db_session.add(event_line_item)
    db_session.commit()

    event_line_item_id = event_line_item.id

    # Delete event
    db_session.delete(event)
    db_session.commit()

    # Verify junction record was cascaded
    junction_record = db_session.query(EventLineItem).filter_by(id=event_line_item_id).first()
    assert junction_record is None

    # Line item should still exist (no cascade from junction table)
    assert db_session.query(LineItem).filter_by(id=line_item.id).first() is not None


def test_deleting_transaction_cascades_to_line_items(db_session):
    """Deleting a transaction cascades to associated line items"""
    # Setup
    payment_method = PaymentMethod(id=generate_id("pm"), name="Test PM", type="credit", is_active=True)
    transaction = Transaction(
        id=generate_id("txn"),
        source="stripe",
        source_id="txn_cascade",
        source_data={},
        transaction_date=datetime.now(UTC),
    )
    db_session.add_all([payment_method, transaction])
    db_session.commit()

    # Create line item
    line_item = LineItem(
        id=generate_id("li"),
        transaction_id=transaction.id,
        date=datetime.now(UTC),
        amount=Decimal("100.00"),
        description="Test",
        payment_method_id=payment_method.id,
    )
    db_session.add(line_item)
    db_session.commit()

    line_item_id = line_item.id

    # Delete transaction
    db_session.delete(transaction)
    db_session.commit()

    # Verify line item was cascaded
    assert db_session.query(LineItem).filter_by(id=line_item_id).first() is None


def test_category_with_events_cannot_be_deleted(db_session, common_fixtures):
    """Category with associated events cannot be deleted"""
    category = common_fixtures["category"]

    # Create event with this category
    event = Event(
        id=generate_id("evt"),
        date=datetime.now(UTC),
        description="Event using category",
        category_id=category.id,
        is_duplicate=False,
    )
    db_session.add(event)
    db_session.commit()

    # Try to delete category - should fail
    with pytest.raises(IntegrityError):
        db_session.delete(category)
        db_session.commit()


def test_payment_method_with_line_items_cannot_be_deleted(db_session):
    """Payment method with associated line items cannot be deleted"""
    # Setup
    payment_method = PaymentMethod(id=generate_id("pm"), name="Protected PM", type="credit", is_active=True)
    transaction = Transaction(
        id=generate_id("txn"),
        source="stripe",
        source_id="stripe_123",
        source_data={},
        transaction_date=datetime.now(UTC),
    )
    db_session.add_all([payment_method, transaction])
    db_session.commit()

    # Create line item using this payment method
    line_item = LineItem(
        id=generate_id("li"),
        transaction_id=transaction.id,
        date=datetime.now(UTC),
        amount=Decimal("75.00"),
        description="Purchase",
        payment_method_id=payment_method.id,
    )
    db_session.add(line_item)
    db_session.commit()

    # Try to delete payment method - should fail
    with pytest.raises(IntegrityError):
        db_session.delete(payment_method)
        db_session.commit()
