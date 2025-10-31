# tests/test_models.py
"""
SQLAlchemy model tests using SQLite in-memory database.

These tests validate model relationships, constraints, and basic behavior.
For PostgreSQL-specific features (JSONB operators, etc.), consider
separate integration tests in CI.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models.sql_models import Base, Event, LineItem, Category, PaymentMethod, Transaction, EventLineItem, Party
from decimal import Decimal
from datetime import datetime, UTC
from utils.id_generator import generate_id

@pytest.fixture
def db_session():
    # Use SQLite in-memory database for testing
    # This provides fast tests without external dependencies (consistent with mongomock approach)
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

def test_create_event_with_line_items(db_session):
    # Create category
    category = Category(id=generate_id("cat"), name='Groceries', is_active=True)
    db_session.add(category)

    # Create payment method
    payment_method = PaymentMethod(id=generate_id("pm"), name='Chase', type='credit', is_active=True)
    db_session.add(payment_method)

    # Create transaction
    transaction = Transaction(
        id=generate_id("txn"),
        source='stripe',
        source_id='txn_test123',
        source_data={},  # JSONB field accepts dict
        transaction_date=datetime.now(UTC)
    )
    db_session.add(transaction)
    db_session.commit()

    # Create line item
    line_item = LineItem(
        id=generate_id("li"),
        transaction_id=transaction.id,
        date=datetime.now(UTC),
        amount=Decimal('50.00'),
        description='Test purchase',
        payment_method_id=payment_method.id
    )
    db_session.add(line_item)
    db_session.commit()

    # Create event
    event = Event(
        id=generate_id("evt"),
        date=datetime.now(UTC),
        description='Test Event',
        category_id=category.id,
        is_duplicate=False
    )
    db_session.add(event)
    db_session.commit()

    # Link line item to event via junction table
    event_line_item = EventLineItem(
        id=generate_id("eli"),
        event_id=event.id,
        line_item_id=line_item.id
    )
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

def test_foreign_key_constraint(db_session):
    # Try to create event with invalid category
    with pytest.raises(IntegrityError):
        event = Event(
            id=generate_id("evt"),
            date=datetime.now(UTC),
            description='Test',
            category_id='cat_nonexistent',
            is_duplicate=False
        )
        db_session.add(event)
        db_session.commit()

def test_event_total_amount_property(db_session):
    """Test that Event.total_amount property correctly sums line items"""
    # Setup category and payment method
    category = Category(id=generate_id("cat"), name='Test Category', is_active=True)
    payment_method = PaymentMethod(id=generate_id("pm"), name='Test Card', type='credit', is_active=True)
    transaction = Transaction(
        id=generate_id("txn"),
        source='manual',
        source_id='test123',
        source_data={},
        transaction_date=datetime.now(UTC)
    )
    db_session.add_all([category, payment_method, transaction])
    db_session.commit()

    # Create event
    event = Event(
        id=generate_id("evt"),
        date=datetime.now(UTC),
        description='Multi-item event',
        category_id=category.id,
        is_duplicate=False
    )
    db_session.add(event)
    db_session.commit()

    # Add multiple line items
    amounts = [Decimal('25.00'), Decimal('30.50'), Decimal('15.25')]
    for amount in amounts:
        line_item = LineItem(
            id=generate_id("li"),
            transaction_id=transaction.id,
            date=datetime.now(UTC),
            amount=amount,
            description='Test item',
            payment_method_id=payment_method.id
        )
        db_session.add(line_item)
        db_session.commit()

        # Link to event
        event_line_item = EventLineItem(
            id=generate_id("eli"),
            event_id=event.id,
            line_item_id=line_item.id
        )
        db_session.add(event_line_item)

    db_session.commit()
    db_session.refresh(event)

    # Verify total
    expected_total = sum(amounts)
    assert event.total_amount == expected_total

def test_event_duplicate_total(db_session):
    """Test that is_duplicate flag causes total to use only first line item"""
    # Setup
    category = Category(id=generate_id("cat"), name='Test', is_active=True)
    payment_method = PaymentMethod(id=generate_id("pm"), name='Test', type='credit', is_active=True)
    transaction = Transaction(
        id=generate_id("txn"),
        source='manual',
        source_id='test',
        source_data={},
        transaction_date=datetime.now(UTC)
    )
    db_session.add_all([category, payment_method, transaction])
    db_session.commit()

    # Create duplicate event
    event = Event(
        id=generate_id("evt"),
        date=datetime.now(UTC),
        description='Duplicate transaction',
        category_id=category.id,
        is_duplicate=True  # Mark as duplicate
    )
    db_session.add(event)
    db_session.commit()

    # Add two line items with different amounts
    amounts = [Decimal('100.00'), Decimal('100.00')]
    for amount in amounts:
        line_item = LineItem(
            id=generate_id("li"),
            transaction_id=transaction.id,
            date=datetime.now(UTC),
            amount=amount,
            description='Duplicate charge',
            payment_method_id=payment_method.id
        )
        db_session.add(line_item)
        db_session.commit()

        event_line_item = EventLineItem(
            id=generate_id("eli"),
            event_id=event.id,
            line_item_id=line_item.id
        )
        db_session.add(event_line_item)

    db_session.commit()
    db_session.refresh(event)

    # With is_duplicate=True, should use first item only
    assert event.total_amount == Decimal('100.00')
    # Not the sum of both (200.00)
    assert event.total_amount != sum(amounts)

def test_cascade_delete_event_deletes_junction_records(db_session):
    """Test that deleting an event cascades to event_line_items"""
    # Setup
    category = Category(id=generate_id("cat"), name='Cascade Test', is_active=True)
    payment_method = PaymentMethod(id=generate_id("pm"), name='Test PM', type='credit', is_active=True)
    transaction = Transaction(
        id=generate_id("txn"),
        source='manual',
        source_id='cascade_test',
        source_data={},
        transaction_date=datetime.now(UTC)
    )
    db_session.add_all([category, payment_method, transaction])
    db_session.commit()

    # Create event and line item
    event = Event(
        id=generate_id("evt"),
        date=datetime.now(UTC),
        description='Test Event',
        category_id=category.id,
        is_duplicate=False
    )
    line_item = LineItem(
        id=generate_id("li"),
        transaction_id=transaction.id,
        date=datetime.now(UTC),
        amount=Decimal('50.00'),
        description='Test item',
        payment_method_id=payment_method.id
    )
    db_session.add_all([event, line_item])
    db_session.commit()

    # Link them
    event_line_item = EventLineItem(
        id=generate_id("eli"),
        event_id=event.id,
        line_item_id=line_item.id
    )
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

def test_cascade_delete_transaction_deletes_line_items(db_session):
    """Test that deleting a transaction cascades to line_items"""
    # Setup
    payment_method = PaymentMethod(id=generate_id("pm"), name='Test PM', type='credit', is_active=True)
    transaction = Transaction(
        id=generate_id("txn"),
        source='stripe',
        source_id='txn_cascade',
        source_data={},
        transaction_date=datetime.now(UTC)
    )
    db_session.add_all([payment_method, transaction])
    db_session.commit()

    # Create line item
    line_item = LineItem(
        id=generate_id("li"),
        transaction_id=transaction.id,
        date=datetime.now(UTC),
        amount=Decimal('100.00'),
        description='Test',
        payment_method_id=payment_method.id
    )
    db_session.add(line_item)
    db_session.commit()

    line_item_id = line_item.id

    # Delete transaction
    db_session.delete(transaction)
    db_session.commit()

    # Verify line item was cascaded
    assert db_session.query(LineItem).filter_by(id=line_item_id).first() is None

def test_set_null_delete_party_nullifies_line_item(db_session):
    """Test that deleting a party sets line_item.party_id to NULL"""
    # Setup
    party = Party(id=generate_id("party"), name='Test Party', is_ignored=False)
    payment_method = PaymentMethod(id=generate_id("pm"), name='Test PM', type='credit', is_active=True)
    transaction = Transaction(
        id=generate_id("txn"),
        source='venmo',
        source_id='venmo_123',
        source_data={},
        transaction_date=datetime.now(UTC)
    )
    db_session.add_all([party, payment_method, transaction])
    db_session.commit()

    # Create line item with party
    line_item = LineItem(
        id=generate_id("li"),
        transaction_id=transaction.id,
        date=datetime.now(UTC),
        amount=Decimal('25.00'),
        description='Payment to party',
        payment_method_id=payment_method.id,
        party_id=party.id
    )
    db_session.add(line_item)
    db_session.commit()

    line_item_id = line_item.id

    # Delete party
    db_session.delete(party)
    db_session.commit()

    # Line item should still exist but party_id should be NULL
    updated_line_item = db_session.query(LineItem).filter_by(id=line_item_id).first()
    assert updated_line_item is not None
    assert updated_line_item.party_id is None

def test_restrict_delete_category_with_events_fails(db_session):
    """Test that deleting a category with events raises an error (RESTRICT)"""
    # Setup
    category = Category(id=generate_id("cat"), name='Protected Category', is_active=True)
    payment_method = PaymentMethod(id=generate_id("pm"), name='Test PM', type='credit', is_active=True)
    transaction = Transaction(
        id=generate_id("txn"),
        source='cash',
        source_id='cash_123',
        source_data={},
        transaction_date=datetime.now(UTC)
    )
    db_session.add_all([category, payment_method, transaction])
    db_session.commit()

    # Create event with this category
    event = Event(
        id=generate_id("evt"),
        date=datetime.now(UTC),
        description='Event using category',
        category_id=category.id,
        is_duplicate=False
    )
    db_session.add(event)
    db_session.commit()

    # Try to delete category - should fail
    with pytest.raises(IntegrityError):
        db_session.delete(category)
        db_session.commit()

def test_restrict_delete_payment_method_with_line_items_fails(db_session):
    """Test that deleting a payment method with line items raises an error (RESTRICT)"""
    # Setup
    payment_method = PaymentMethod(id=generate_id("pm"), name='Protected PM', type='credit', is_active=True)
    transaction = Transaction(
        id=generate_id("txn"),
        source='stripe',
        source_id='stripe_123',
        source_data={},
        transaction_date=datetime.now(UTC)
    )
    db_session.add_all([payment_method, transaction])
    db_session.commit()

    # Create line item using this payment method
    line_item = LineItem(
        id=generate_id("li"),
        transaction_id=transaction.id,
        date=datetime.now(UTC),
        amount=Decimal('75.00'),
        description='Purchase',
        payment_method_id=payment_method.id
    )
    db_session.add(line_item)
    db_session.commit()

    # Try to delete payment method - should fail
    with pytest.raises(IntegrityError):
        db_session.delete(payment_method)
        db_session.commit()
