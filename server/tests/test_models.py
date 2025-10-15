# tests/test_models.py
import pytest
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models.sql_models import Base, Event, LineItem, Category, PaymentMethod, Transaction, EventLineItem
from decimal import Decimal
from datetime import datetime
from utils.id_generator import generate_id

@pytest.fixture
def db_session():
    # In-memory SQLite for tests
    engine = create_engine('sqlite:///:memory:')

    # Enable foreign key constraints in SQLite
    @sqlalchemy.event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

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
        source_data='{}',
        transaction_date=datetime.now()
    )
    db_session.add(transaction)
    db_session.commit()

    # Create line item
    line_item = LineItem(
        id=generate_id("li"),
        transaction_id=transaction.id,
        date=datetime.now(),
        amount=Decimal('50.00'),
        description='Test purchase',
        payment_method_id=payment_method.id
    )
    db_session.add(line_item)
    db_session.commit()

    # Create event
    event = Event(
        id=generate_id("evt"),
        date=datetime.now(),
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
            date=datetime.now(),
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
        source_data='{}',
        transaction_date=datetime.now()
    )
    db_session.add_all([category, payment_method, transaction])
    db_session.commit()

    # Create event
    event = Event(
        id=generate_id("evt"),
        date=datetime.now(),
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
            date=datetime.now(),
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
        source_data='{}',
        transaction_date=datetime.now()
    )
    db_session.add_all([category, payment_method, transaction])
    db_session.commit()

    # Create duplicate event
    event = Event(
        id=generate_id("evt"),
        date=datetime.now(),
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
            date=datetime.now(),
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
