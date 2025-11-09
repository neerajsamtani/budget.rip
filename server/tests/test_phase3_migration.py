"""
Unit tests for Phase 3 migration scripts and utilities.

Tests:
- Dual-write utility functions
- Transaction migration logic
- Line item migration logic
- Verification checks
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import mongomock
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from models.sql_models import Base, LineItem, PaymentMethod, Transaction
from utils.dual_write import DualWriteError, dual_write_operation
from utils.id_generator import generate_id


@pytest.fixture
def pg_session():
    """Create an in-memory PostgreSQL-like SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")

    # Enable foreign key constraints in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def mongo_db():
    """Create a mock MongoDB database for testing"""
    client = mongomock.MongoClient()
    db = client["test_db"]
    return db


@pytest.fixture
def sample_payment_method(pg_session):
    """Create a sample payment method for tests"""
    pm = PaymentMethod(id=generate_id("pm"), name="Test Card", type="credit", is_active=True)
    pg_session.add(pm)
    pg_session.commit()
    return pm


class TestDualWriteUtility:
    """Test dual-write utility functions"""

    def test_dual_write_operation_success(self):
        """Test successful dual-write to both databases"""
        mongo_result = {"_id": "123"}
        pg_result = {"id": "txn_456"}

        # Mock functions
        mongo_write = MagicMock(return_value=mongo_result)
        pg_write = MagicMock(return_value=pg_result)

        # Execute dual-write
        result = dual_write_operation(
            mongo_write_func=mongo_write,
            pg_write_func=pg_write,
            operation_name="test_operation",
        )

        # Verify both writes were called
        assert mongo_write.called
        assert pg_write.called

        # Verify result
        assert result["success"] is True
        assert result["mongo_success"] is True
        assert result["pg_success"] is True
        assert result["mongo_result"] == mongo_result
        assert result["pg_result"] == pg_result

    def test_dual_write_mongo_failure(self):
        """Test dual-write when MongoDB write fails"""
        # Mock MongoDB failure
        mongo_write = MagicMock(side_effect=Exception("MongoDB error"))
        pg_write = MagicMock()

        # Execute dual-write - should raise exception
        with pytest.raises(DualWriteError):
            dual_write_operation(
                mongo_write_func=mongo_write,
                pg_write_func=pg_write,
                operation_name="test_operation",
            )

        # PostgreSQL write should not be called
        assert not pg_write.called

    def test_dual_write_pg_failure_non_critical(self):
        """Test dual-write when PostgreSQL write fails (non-critical)"""
        mongo_result = {"_id": "123"}

        # Mock PostgreSQL failure
        mongo_write = MagicMock(return_value=mongo_result)
        pg_write = MagicMock(side_effect=Exception("PostgreSQL error"))

        # Execute dual-write - should succeed despite PG failure
        result = dual_write_operation(
            mongo_write_func=mongo_write,
            pg_write_func=pg_write,
            operation_name="test_operation",
            critical=False,
        )

        # MongoDB write should succeed
        assert result["success"] is True
        assert result["mongo_success"] is True
        assert result["pg_success"] is False
        assert result["pg_error"] is not None

    def test_dual_write_pg_failure_critical(self):
        """Test dual-write when PostgreSQL write fails (critical)"""
        mongo_result = {"_id": "123"}

        # Mock PostgreSQL failure
        mongo_write = MagicMock(return_value=mongo_result)
        pg_write = MagicMock(side_effect=Exception("PostgreSQL error"))

        # Execute dual-write with critical=True - should raise exception
        with pytest.raises(DualWriteError):
            dual_write_operation(
                mongo_write_func=mongo_write,
                pg_write_func=pg_write,
                operation_name="test_operation",
                critical=True,
            )


class TestTransactionMigration:
    """Test transaction migration logic"""

    def test_venmo_transaction_date_extraction(self):
        """Test extracting transaction date from Venmo data"""
        from migrations.phase3_migrate_transactions import get_transaction_date

        venmo_transaction = {
            "_id": "123",
            "date_created": 1609459200.0,  # 2021-01-01 00:00:00 UTC
        }

        date = get_transaction_date(venmo_transaction, "venmo")

        assert isinstance(date, datetime)
        assert date.year == 2021
        assert date.month == 1
        assert date.day == 1

    def test_splitwise_transaction_date_extraction(self):
        """Test extracting transaction date from Splitwise data"""
        from migrations.phase3_migrate_transactions import get_transaction_date

        splitwise_transaction = {
            "_id": "123",
            "date": "2021-01-01T00:00:00Z",
        }

        date = get_transaction_date(splitwise_transaction, "splitwise")

        assert isinstance(date, datetime)
        assert date.year == 2021
        assert date.month == 1
        assert date.day == 1

    def test_stripe_transaction_date_extraction(self):
        """Test extracting transaction date from Stripe data"""
        from migrations.phase3_migrate_transactions import get_transaction_date

        stripe_transaction = {
            "_id": "123",
            "transacted_at": 1609459200,  # 2021-01-01 00:00:00 UTC
        }

        date = get_transaction_date(stripe_transaction, "stripe")

        assert isinstance(date, datetime)
        assert date.year == 2021

    def test_cash_transaction_date_extraction(self):
        """Test extracting transaction date from cash data"""
        from migrations.phase3_migrate_transactions import get_transaction_date

        cash_transaction = {
            "_id": "123",
            "date": 1609459200.0,
        }

        date = get_transaction_date(cash_transaction, "cash")

        assert isinstance(date, datetime)
        assert date.year == 2021

    def test_transaction_creation(self, pg_session):
        """Test creating a transaction in PostgreSQL"""
        txn = Transaction(
            id=generate_id("txn"),
            source="venmo",
            source_id="mongo_123",
            source_data={"amount": 50.0, "note": "Test"},
            transaction_date=datetime.now(UTC),
        )

        pg_session.add(txn)
        pg_session.commit()

        # Verify transaction was created
        saved_txn = pg_session.query(Transaction).filter_by(source_id="mongo_123").first()

        assert saved_txn is not None
        assert saved_txn.source == "venmo"
        assert saved_txn.source_data["amount"] == 50.0

    def test_transaction_unique_constraint(self, pg_session):
        """Test that duplicate transactions are prevented"""
        txn1 = Transaction(
            id=generate_id("txn"),
            source="venmo",
            source_id="mongo_123",
            source_data={"amount": 50.0},
            transaction_date=datetime.now(UTC),
        )

        pg_session.add(txn1)
        pg_session.commit()

        # Try to create duplicate
        from sqlalchemy.exc import IntegrityError

        txn2 = Transaction(
            id=generate_id("txn"),
            source="venmo",
            source_id="mongo_123",  # Same source and source_id
            source_data={"amount": 75.0},
            transaction_date=datetime.now(UTC),
        )

        pg_session.add(txn2)

        with pytest.raises(IntegrityError):
            pg_session.commit()


class TestLineItemMigration:
    """Test line item migration logic"""

    def test_line_item_creation(self, pg_session, sample_payment_method):
        """Test creating a line item in PostgreSQL"""
        # Create transaction first
        txn = Transaction(
            id=generate_id("txn"),
            source="venmo",
            source_id="mongo_123",
            source_data={"amount": 50.0},
            transaction_date=datetime.now(UTC),
        )
        pg_session.add(txn)
        pg_session.commit()

        # Create line item
        line_item = LineItem(
            id=generate_id("li"),
            transaction_id=txn.id,
            mongo_id="line_item_mongo_123",
            date=datetime.now(UTC),
            amount=Decimal("50.00"),
            description="Test purchase",
            payment_method_id=sample_payment_method.id,
        )

        pg_session.add(line_item)
        pg_session.commit()

        # Verify line item was created
        saved_item = pg_session.query(LineItem).filter_by(mongo_id="line_item_mongo_123").first()

        assert saved_item is not None
        assert saved_item.amount == Decimal("50.00")
        assert saved_item.description == "Test purchase"

    def test_line_item_foreign_key_constraint(self, pg_session, sample_payment_method):
        """Test that line items require valid transaction_id"""
        from sqlalchemy.exc import IntegrityError

        # Try to create line item with invalid transaction_id
        line_item = LineItem(
            id=generate_id("li"),
            transaction_id="invalid_txn_id",
            mongo_id="line_item_mongo_123",
            date=datetime.now(UTC),
            amount=Decimal("50.00"),
            description="Test purchase",
            payment_method_id=sample_payment_method.id,
        )

        pg_session.add(line_item)

        with pytest.raises(IntegrityError):
            pg_session.commit()

    def test_line_item_cascade_delete(self, pg_session, sample_payment_method):
        """Test that deleting transaction cascades to line items"""
        # Create transaction
        txn = Transaction(
            id=generate_id("txn"),
            source="venmo",
            source_id="mongo_123",
            source_data={"amount": 50.0},
            transaction_date=datetime.now(UTC),
        )
        pg_session.add(txn)
        pg_session.commit()

        # Create line item
        line_item = LineItem(
            id=generate_id("li"),
            transaction_id=txn.id,
            mongo_id="line_item_mongo_123",
            date=datetime.now(UTC),
            amount=Decimal("50.00"),
            description="Test purchase",
            payment_method_id=sample_payment_method.id,
        )
        pg_session.add(line_item)
        pg_session.commit()

        # Delete transaction
        pg_session.delete(txn)
        pg_session.commit()

        # Verify line item was cascade deleted
        saved_item = pg_session.query(LineItem).filter_by(mongo_id="line_item_mongo_123").first()

        assert saved_item is None


class TestMigrationIntegration:
    """Integration tests for complete migration flow"""

    def test_end_to_end_venmo_migration(self, mongo_db, pg_session, sample_payment_method):
        """Test complete Venmo transaction and line item migration"""
        # Setup MongoDB data
        venmo_collection = mongo_db["venmo_raw_data"]
        venmo_doc = {
            "_id": "venmo_123",
            "date_created": 1609459200.0,
            "amount": 50.0,
            "note": "Coffee",
            "actor": {"first_name": "Alice"},
            "target": {"first_name": "Bob"},
        }
        venmo_collection.insert_one(venmo_doc)

        line_items_collection = mongo_db["line_items"]
        line_item_doc = {
            "_id": "line_item_venmo_123",
            "date": 1609459200.0,
            "amount": 50.0,
            "description": "Coffee",
            "payment_method": "Test Card",
        }
        line_items_collection.insert_one(line_item_doc)

        # Migrate transaction
        txn = Transaction(
            id=generate_id("txn"),
            source="venmo",
            source_id="venmo_123",
            source_data=venmo_doc,
            transaction_date=datetime.fromtimestamp(1609459200.0, UTC),
        )
        pg_session.add(txn)
        pg_session.commit()

        # Migrate line item
        line_item = LineItem(
            id=generate_id("li"),
            transaction_id=txn.id,
            mongo_id="line_item_venmo_123",
            date=datetime.fromtimestamp(1609459200.0, UTC),
            amount=Decimal("50.00"),
            description="Coffee",
            payment_method_id=sample_payment_method.id,
        )
        pg_session.add(line_item)
        pg_session.commit()

        # Verify data
        assert pg_session.query(Transaction).count() == 1
        assert pg_session.query(LineItem).count() == 1

        saved_txn = pg_session.query(Transaction).first()
        assert saved_txn.source == "venmo"
        assert saved_txn.source_data["amount"] == 50.0

        saved_item = pg_session.query(LineItem).first()
        assert saved_item.amount == Decimal("50.00")
        assert saved_item.transaction_id == txn.id

    def test_orphaned_line_item_handling(self, mongo_db, pg_session, sample_payment_method):
        """Test creating manual transaction for orphaned line items"""
        # Create line item without corresponding transaction

        # Create manual transaction
        manual_txn = Transaction(
            id=generate_id("txn"),
            source="manual",
            source_id="manual_orphaned_line_item",
            source_data={
                "description": "Manual entry",
                "amount": 25.0,
                "note": "Created for orphaned line item",
            },
            transaction_date=datetime.fromtimestamp(1609459200.0, UTC),
        )
        pg_session.add(manual_txn)
        pg_session.commit()

        # Create line item linked to manual transaction
        line_item = LineItem(
            id=generate_id("li"),
            transaction_id=manual_txn.id,
            mongo_id="orphaned_line_item",
            date=datetime.fromtimestamp(1609459200.0, UTC),
            amount=Decimal("25.00"),
            description="Manual entry",
            payment_method_id=sample_payment_method.id,
        )
        pg_session.add(line_item)
        pg_session.commit()

        # Verify
        assert pg_session.query(Transaction).filter_by(source="manual").count() == 1
        assert pg_session.query(LineItem).filter_by(mongo_id="orphaned_line_item").first() is not None


class TestPaymentMethodLookup:
    """Test payment method lookup and creation"""

    def test_payment_method_lookup_by_name(self, pg_session):
        """Test looking up payment method by name"""
        pm = PaymentMethod(id=generate_id("pm"), name="Chase Sapphire", type="credit", is_active=True)
        pg_session.add(pm)
        pg_session.commit()

        # Lookup
        found = pg_session.query(PaymentMethod).filter_by(name="Chase Sapphire").first()

        assert found is not None
        assert found.id == pm.id

    def test_unknown_payment_method_creation(self, pg_session):
        """Test creating Unknown payment method when needed"""
        # Create Unknown payment method
        unknown_pm = PaymentMethod(id=generate_id("pm"), name="Unknown", type="cash", is_active=True)
        pg_session.add(unknown_pm)
        pg_session.commit()

        # Verify
        found = pg_session.query(PaymentMethod).filter_by(name="Unknown").first()
        assert found is not None
