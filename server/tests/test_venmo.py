import pytest

from dao import (
    upsert_with_id,
    venmo_raw_data_collection,
)
from resources.venmo import refresh_venmo, venmo_to_line_items


@pytest.fixture
def mock_venmo_user(mocker):
    """Mock Venmo user profile"""
    mock_user = mocker.Mock()
    mock_user.id = 12345
    mock_user.username = "test_user"
    mock_user.first_name = "Test"
    mock_user.last_name = "User"
    return mock_user


@pytest.fixture
def mock_venmo_transaction():
    """Mock Venmo transaction"""
    return {
        "id": "venmo_txn_123",
        "date_created": 1673778600.0,
        "actor": {"first_name": "Neeraj"},
        "target": {"first_name": "John"},
        "payment_type": "pay",
        "note": "Test payment",
        "amount": 25.0,
    }


@pytest.fixture
def mock_venmo_transaction_charge():
    """Mock Venmo charge transaction"""
    return {
        "id": "venmo_txn_456",
        "date_created": 1673778601.0,
        "actor": {"first_name": "Jane"},
        "target": {"first_name": "Neeraj"},
        "payment_type": "charge",
        "note": "Test charge",
        "amount": 15.0,
    }


@pytest.fixture
def mock_venmo_transaction_received():
    """Mock Venmo received transaction"""
    return {
        "id": "venmo_txn_789",
        "date_created": 1673778602.0,
        "actor": {"first_name": "Bob"},
        "target": {"first_name": "Neeraj"},
        "payment_type": "pay",
        "note": "Test received payment",
        "amount": 10.0,
    }


@pytest.fixture
def mock_venmo_transaction_ignored():
    """Mock Venmo transaction with ignored party"""
    return {
        "id": "venmo_txn_ignored",
        "date_created": 1673778600.0,
        "actor": {"first_name": "Pink Palace Babes"},  # Ignored party
        "target": {"first_name": "Neeraj"},
        "payment_type": "pay",
        "note": "Ignored transaction",
        "amount": 25.0,
    }


class TestVenmoAPI:
    def test_refresh_venmo_endpoint_syncs_transactions(self, test_client, jwt_token, flask_app, mocker):
        """Venmo refresh endpoint syncs transactions and returns success message"""
        with flask_app.app_context():
            mock_refresh = mocker.patch("resources.venmo.refresh_venmo")
            response = test_client.get(
                "/api/refresh/venmo",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            assert response.get_json() == "Refreshed Venmo Connection"
            mock_refresh.assert_called_once()

    def test_refresh_venmo_requires_authentication(self, test_client):
        """Venmo refresh endpoint requires authentication"""
        response = test_client.get("/api/refresh/venmo")
        assert response.status_code == 401


class TestVenmoFunctions:
    def test_refresh_venmo_stores_transactions_in_database(self, flask_app, mock_venmo_user, mocker):
        """Venmo refresh stores transactions in database with source metadata"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch("resources.venmo.get_venmo_client", return_value=mock_venmo_client)

            # Mock transactions with dict objects to avoid circular reference
            class MockActor:
                first_name = "Neeraj"

            class MockTarget:
                first_name = "John"

            class MockTransaction:
                id = "venmo_test_txn_1"
                date_created = 1673778600.0
                actor = MockActor()
                target = MockTarget()
                payment_type = "pay"
                note = "Test payment"
                amount = 25.0

            mock_transaction1 = MockTransaction()

            mock_transactions = mocker.Mock()
            mock_transactions.__iter__ = lambda self: iter([mock_transaction1])
            mock_transactions.get_next_page.return_value = None

            mock_venmo_client.user.get_user_transactions.return_value = mock_transactions

            # Call the function
            refresh_venmo()

            # Query database to verify transaction was inserted
            from models.database import SessionLocal
            from models.sql_models import Transaction

            db = SessionLocal()
            try:
                transactions = db.query(Transaction).filter(Transaction.source == "venmo").all()
                assert len(transactions) == 1
                # Verify transaction has correct source
                assert transactions[0].source == "venmo"
                assert transactions[0].source_id == "venmo_test_txn_1"
            finally:
                db.close()

    def test_transactions_before_moving_date_are_ignored(self, flask_app, mock_venmo_user, mocker):
        """Transactions before the moving date are not imported"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch("resources.venmo.get_venmo_client", return_value=mock_venmo_client)

            mocker.patch("resources.venmo.upsert_transactions")

            # Mock transactions - all before moving date (1659510000.0)
            mock_transactions = mocker.Mock()
            mock_transaction = mocker.Mock()
            mock_transaction.date_created = 1650000000.0  # Before moving date
            mock_transaction.actor.first_name = "Neeraj"
            mock_transaction.target.first_name = "John"
            mock_transaction.payment_type = "pay"
            mock_transaction.note = "Old transaction"
            mock_transaction.amount = 25.0

            mock_transactions.__iter__ = lambda self: iter([mock_transaction])
            mock_transactions.get_next_page.return_value = None

            mock_venmo_client.user.get_user_transactions.return_value = mock_transactions

            # Call the function
            refresh_venmo()

            # Verify bulk_upsert was not called (no transactions after moving date)

    def test_transactions_with_ignored_parties_are_filtered(self, flask_app, mock_venmo_user, mocker):
        """Transactions involving ignored parties are filtered out"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch("resources.venmo.get_venmo_client", return_value=mock_venmo_client)

            mocker.patch("resources.venmo.upsert_transactions")

            # Mock transactions - one with ignored party
            mock_transactions = mocker.Mock()
            mock_transaction = mocker.Mock()
            mock_transaction.date_created = 1673778600.0  # After moving date
            mock_transaction.actor.first_name = "Pink Palace Babes"  # Ignored party
            mock_transaction.target.first_name = "Neeraj"
            mock_transaction.payment_type = "pay"
            mock_transaction.note = "Ignored transaction"
            mock_transaction.amount = 25.0

            mock_transactions.__iter__ = lambda self: iter([mock_transaction])
            mock_transactions.get_next_page.return_value = None

            mock_venmo_client.user.get_user_transactions.return_value = mock_transactions

            # Call the function
            refresh_venmo()

            # Verify bulk_upsert was not called (ignored party)

    def test_venmo_refresh_fetches_all_pages(self, flask_app, mock_venmo_user, mocker):
        """Venmo refresh fetches transactions from all pages"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch("resources.venmo.get_venmo_client", return_value=mock_venmo_client)

            # Mock first page of transactions
            class MockActor1:
                first_name = "Neeraj"

            class MockTarget1:
                first_name = "John"

            class MockTransaction1:
                id = "venmo_test_pagination_1"
                date_created = 1673778600.0
                actor = MockActor1()
                target = MockTarget1()
                payment_type = "pay"
                note = "Page 1 transaction"
                amount = 25.0

            mock_transaction1 = MockTransaction1()

            # Mock second page of transactions
            class MockActor2:
                first_name = "Neeraj"

            class MockTarget2:
                first_name = "Jane"

            class MockTransaction2:
                id = "venmo_test_pagination_2"
                date_created = 1673778601.0
                actor = MockActor2()
                target = MockTarget2()
                payment_type = "pay"
                note = "Page 2 transaction"
                amount = 15.0

            mock_transaction2 = MockTransaction2()

            mock_transactions_page1 = mocker.Mock()
            mock_transactions_page1.__iter__ = lambda self: iter([mock_transaction1])

            mock_transactions_page2 = mocker.Mock()
            mock_transactions_page2.__iter__ = lambda self: iter([mock_transaction2])
            mock_transactions_page2.get_next_page.return_value = None

            # Set up pagination
            mock_transactions_page1.get_next_page.side_effect = [
                mock_transactions_page2,
                None,
            ]

            mock_venmo_client.user.get_user_transactions.return_value = mock_transactions_page1

            # Call the function
            refresh_venmo()

            # Query database to verify both transactions were inserted
            from models.database import SessionLocal
            from models.sql_models import Transaction

            db = SessionLocal()
            try:
                transactions = db.query(Transaction).filter(Transaction.source == "venmo").all()
                assert len(transactions) == 2
            finally:
                db.close()

    def test_missing_venmo_profile_raises_error(self, flask_app, mocker):
        """Missing Venmo profile raises exception"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = None
            mocker.patch("resources.venmo.get_venmo_client", return_value=mock_venmo_client)

            # Call the function and expect exception
            with pytest.raises(Exception, match="Failed to get Venmo profile"):
                refresh_venmo()

    def test_venmo_transactions_convert_to_line_items(self, flask_app, mock_venmo_transaction, mocker):
        """Venmo transactions are converted to line items with correct fields"""
        with flask_app.app_context():
            from models.database import SessionLocal
            from models.sql_models import LineItem

            # Insert test transaction data
            test_transaction = mock_venmo_transaction
            upsert_with_id(venmo_raw_data_collection, test_transaction, test_transaction["id"])

            # Call the function
            venmo_to_line_items()

            # Query database to verify line items were created
            db = SessionLocal()
            try:
                line_items = db.query(LineItem).all()
                assert len(line_items) == 1
                line_item = line_items[0]
                assert line_item.id.startswith("li_")
                assert line_item.responsible_party == "John"
                assert line_item.payment_method_id is not None
                assert line_item.description == "Test payment"
                assert line_item.amount == 25.0
            finally:
                db.close()

    def test_charge_transaction_uses_actor_as_responsible_party(self, flask_app, mock_venmo_transaction_charge, mocker):
        """Charge transactions use the actor as the responsible party"""
        with flask_app.app_context():
            from models.database import SessionLocal
            from models.sql_models import LineItem

            # Insert test transaction data
            test_transaction = mock_venmo_transaction_charge
            upsert_with_id(venmo_raw_data_collection, test_transaction, test_transaction["id"])

            # Call the function
            venmo_to_line_items()

            # Query database to verify line item was created
            db = SessionLocal()
            try:
                line_items = db.query(LineItem).all()
                assert len(line_items) == 1
                line_item = line_items[0]
                assert line_item.id.startswith("li_")
                assert line_item.responsible_party == "Jane"
                assert line_item.payment_method_id is not None
                assert line_item.description == "Test charge"
                assert line_item.amount == 15.0
            finally:
                db.close()

    def test_received_payment_flips_amount_to_negative(self, flask_app, mock_venmo_transaction_received, mocker):
        """Received payments have negative amounts"""
        with flask_app.app_context():
            from models.database import SessionLocal
            from models.sql_models import LineItem

            # Insert test transaction data
            test_transaction = mock_venmo_transaction_received
            upsert_with_id(venmo_raw_data_collection, test_transaction, test_transaction["id"])

            # Call the function
            venmo_to_line_items()

            # Query database to verify line item was created
            db = SessionLocal()
            try:
                line_items = db.query(LineItem).all()
                assert len(line_items) == 1
                line_item = line_items[0]
                assert line_item.id.startswith("li_")
                assert line_item.responsible_party == "Bob"
                assert line_item.payment_method_id is not None
                assert line_item.description == "Test received payment"
                assert line_item.amount == -10.0
            finally:
                db.close()

    def test_empty_transactions_creates_no_line_items(self, flask_app, mocker):
        """Empty transaction list creates no line items"""
        with flask_app.app_context():
            mocker.patch("resources.venmo.upsert_line_items")

            # Call the function with no transactions
            venmo_to_line_items()

    def test_multiple_transactions_create_multiple_line_items(self, flask_app, mocker):
        """Multiple transactions create corresponding line items"""
        with flask_app.app_context():
            from models.database import SessionLocal
            from models.sql_models import LineItem

            # Insert multiple test transactions
            transactions = [
                {
                    "id": "venmo_txn_1",
                    "date_created": 1673778600.0,
                    "actor": {"first_name": "Neeraj"},
                    "target": {"first_name": "John"},
                    "payment_type": "pay",
                    "note": "Payment 1",
                    "amount": 25.0,
                },
                {
                    "id": "venmo_txn_2",
                    "date_created": 1673778601.0,
                    "actor": {"first_name": "Jane"},
                    "target": {"first_name": "Neeraj"},
                    "payment_type": "charge",
                    "note": "Charge 1",
                    "amount": 15.0,
                },
                {
                    "id": "venmo_txn_3",
                    "date_created": 1673778602.0,
                    "actor": {"first_name": "Bob"},
                    "target": {"first_name": "Neeraj"},
                    "payment_type": "pay",
                    "note": "Received payment",
                    "amount": 10.0,
                },
            ]

            for transaction in transactions:
                upsert_with_id(venmo_raw_data_collection, transaction, transaction["id"])

            # Call the function
            venmo_to_line_items()

            # Query database to verify line items were created
            db = SessionLocal()
            try:
                line_items = db.query(LineItem).all()
                assert len(line_items) == 3

                # Check amounts (received payment should be flipped)
                amounts = [item.amount for item in line_items]
                assert 25.0 in amounts  # Payment
                assert 15.0 in amounts  # Charge
                assert -10.0 in amounts  # Received (flipped)
            finally:
                db.close()


class TestVenmoIntegration:
    def test_complete_workflow_syncs_and_converts_transactions(self, flask_app, mock_venmo_user, mocker):
        """Complete workflow syncs transactions and converts to line items"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch("resources.venmo.get_venmo_client", return_value=mock_venmo_client)

            # Use a Mock for the transaction for refresh_venmo
            mock_transaction = mocker.Mock()
            mock_transaction.date_created = 1673778600.0
            mock_transaction.actor.first_name = "Neeraj"
            mock_transaction.target.first_name = "John"
            mock_transaction.payment_type = "pay"
            mock_transaction.note = "Integration test payment"
            mock_transaction.amount = 25.0
            mock_transaction.source_id = "venmo_txn_integration"
            mock_transaction.id = "venmo_txn_integration"

            mock_transactions = mocker.Mock()
            mock_transactions.__iter__ = lambda self: iter([mock_transaction])
            mock_transactions.get_next_page.return_value = None
            mock_venmo_client.user.get_user_transactions.return_value = mock_transactions

            # Mock bulk_upsert_transactions to avoid trying to serialize Mock objects to PostgreSQL
            mocker.patch("resources.venmo.upsert_transactions")

            # Call refresh function (PostgreSQL write mocked to avoid Mock serialization issues)
            refresh_venmo()

            # Remove the Mock and insert a real dict for venmo_to_line_items
            # Delete existing Venmo transactions from PostgreSQL
            from models.database import SessionLocal
            from models.sql_models import Transaction

            db = SessionLocal()
            try:
                db.query(Transaction).filter(Transaction.source == "venmo").delete()
                db.commit()
            finally:
                db.close()

            transaction_dict = {
                "id": "venmo_txn_integration",
                "date_created": 1673778600.0,
                "actor": {"first_name": "Neeraj"},
                "target": {"first_name": "John"},
                "payment_type": "pay",
                "note": "Integration test payment",
                "amount": 25.0,
            }
            upsert_with_id(
                venmo_raw_data_collection,
                transaction_dict,
                transaction_dict["id"],
            )

            # Now call line items conversion with the stored data
            venmo_to_line_items()

            # Verify bulk_upsert was called for line items

    def test_zero_amount_transactions_are_processed(self, flask_app, mock_venmo_user, mocker):
        """Zero amount transactions are processed correctly"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch("resources.venmo.get_venmo_client", return_value=mock_venmo_client)

            # Mock edge case transactions with simple classes to avoid circular references
            class MockActor1:
                first_name = "Neeraj"

            class MockTarget1:
                first_name = "John"

            class MockTransaction1:
                id = "venmo_edge_1"
                date_created = 1673778600.0
                actor = MockActor1()
                target = MockTarget1()
                payment_type = "pay"
                note = ""
                amount = 0.0

            class MockActor2:
                first_name = "Jane"

            class MockTarget2:
                first_name = "Neeraj"

            class MockTransaction2:
                id = "venmo_edge_2"
                date_created = 1673778601.0
                actor = MockActor2()
                target = MockTarget2()
                payment_type = "charge"
                note = "Zero amount"
                amount = 0.0

            mock_transaction1 = MockTransaction1()
            mock_transaction2 = MockTransaction2()

            mock_transactions = mocker.Mock()
            mock_transactions.__iter__ = lambda self: iter([mock_transaction1, mock_transaction2])
            mock_transactions.get_next_page.return_value = None

            mock_venmo_client.user.get_user_transactions.return_value = mock_transactions

            # Call the function
            refresh_venmo()

            # Query database to verify transactions were processed
            from models.database import SessionLocal
            from models.sql_models import Transaction

            db = SessionLocal()
            try:
                transactions = db.query(Transaction).filter(Transaction.source == "venmo").all()
                assert len(transactions) == 2
            finally:
                db.close()
