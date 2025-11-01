import pytest

from dao import (
    get_collection,
    line_items_collection,
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
        "_id": "venmo_txn_123",
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
        "_id": "venmo_txn_456",
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
        "_id": "venmo_txn_789",
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
        "_id": "venmo_txn_ignored",
        "date_created": 1673778600.0,
        "actor": {"first_name": "Pink Palace Babes"},  # Ignored party
        "target": {"first_name": "Neeraj"},
        "payment_type": "pay",
        "note": "Ignored transaction",
        "amount": 25.0,
    }


class TestVenmoAPI:
    def test_refresh_venmo_api_success(self, test_client, jwt_token, flask_app, mocker):
        """Test GET /api/refresh/venmo endpoint - success case"""
        with flask_app.app_context():
            mock_refresh = mocker.patch("resources.venmo.refresh_venmo")
            mock_venmo_to_line_items = mocker.patch(
                "resources.venmo.venmo_to_line_items"
            )
            response = test_client.get(
                "/api/refresh/venmo",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            assert response.get_json() == "Refreshed Venmo Connection"
            mock_refresh.assert_called_once()
            mock_venmo_to_line_items.assert_called_once()

    def test_refresh_venmo_api_unauthorized(self, test_client):
        """Test GET /api/refresh/venmo endpoint - unauthorized"""
        response = test_client.get("/api/refresh/venmo")
        assert response.status_code == 401


class TestVenmoFunctions:
    def test_refresh_venmo_success(self, flask_app, mock_venmo_user, mocker):
        """Test refresh_venmo function - success case"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch(
                "resources.venmo.get_venmo_client", return_value=mock_venmo_client
            )

            # Mock bulk_upsert
            mock_bulk_upsert = mocker.patch("resources.venmo.bulk_upsert")

            # Mock transactions
            mock_transactions = mocker.Mock()
            mock_transaction1 = mocker.Mock()
            mock_transaction1.date_created = (
                1673778600.0  # After moving date (1659510000.0)
            )
            mock_transaction1.actor.first_name = "Neeraj"
            mock_transaction1.target.first_name = "John"
            mock_transaction1.payment_type = "pay"
            mock_transaction1.note = "Test payment"
            mock_transaction1.amount = 25.0

            mock_transactions.__iter__ = lambda self: iter([mock_transaction1])
            mock_transactions.get_next_page.return_value = None

            mock_venmo_client.user.get_user_transactions.return_value = (
                mock_transactions
            )

            # Call the function
            refresh_venmo()

            # Verify bulk_upsert was called with the transaction after moving date
            mock_bulk_upsert.assert_called_once()
            call_args = mock_bulk_upsert.call_args
            assert call_args[0][0] == venmo_raw_data_collection

            transactions = call_args[0][1]
            assert len(transactions) == 1
            assert transactions[0].note == "Test payment"

    def test_refresh_venmo_ignores_old_transactions(
        self, flask_app, mock_venmo_user, mocker
    ):
        """Test refresh_venmo function - ignores transactions before moving date"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch(
                "resources.venmo.get_venmo_client", return_value=mock_venmo_client
            )

            # Mock bulk_upsert
            mock_bulk_upsert = mocker.patch("resources.venmo.bulk_upsert")

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

            mock_venmo_client.user.get_user_transactions.return_value = (
                mock_transactions
            )

            # Call the function
            refresh_venmo()

            # Verify bulk_upsert was not called (no transactions after moving date)
            mock_bulk_upsert.assert_not_called()

    def test_refresh_venmo_ignores_parties_to_ignore(
        self, flask_app, mock_venmo_user, mocker
    ):
        """Test refresh_venmo function - ignores transactions with parties to ignore"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch(
                "resources.venmo.get_venmo_client", return_value=mock_venmo_client
            )

            # Mock bulk_upsert
            mock_bulk_upsert = mocker.patch("resources.venmo.bulk_upsert")

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

            mock_venmo_client.user.get_user_transactions.return_value = (
                mock_transactions
            )

            # Call the function
            refresh_venmo()

            # Verify bulk_upsert was not called (ignored party)
            mock_bulk_upsert.assert_not_called()

    def test_refresh_venmo_handles_pagination(self, flask_app, mock_venmo_user, mocker):
        """Test refresh_venmo function - handles pagination correctly"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch(
                "resources.venmo.get_venmo_client", return_value=mock_venmo_client
            )

            # Mock bulk_upsert
            mock_bulk_upsert = mocker.patch("resources.venmo.bulk_upsert")

            # Mock first page of transactions
            mock_transactions_page1 = mocker.Mock()
            mock_transaction1 = mocker.Mock()
            mock_transaction1.date_created = 1673778600.0
            mock_transaction1.actor.first_name = "Neeraj"
            mock_transaction1.target.first_name = "John"
            mock_transaction1.payment_type = "pay"
            mock_transaction1.note = "Page 1 transaction"
            mock_transaction1.amount = 25.0

            mock_transactions_page1.__iter__ = lambda self: iter([mock_transaction1])
            mock_transactions_page1.get_next_page.return_value = mock_transactions_page1

            # Mock second page of transactions
            mock_transactions_page2 = mocker.Mock()
            mock_transaction2 = mocker.Mock()
            mock_transaction2.date_created = 1673778601.0
            mock_transaction2.actor.first_name = "Neeraj"
            mock_transaction2.target.first_name = "Jane"
            mock_transaction2.payment_type = "pay"
            mock_transaction2.note = "Page 2 transaction"
            mock_transaction2.amount = 15.0

            mock_transactions_page2.__iter__ = lambda self: iter([mock_transaction2])
            mock_transactions_page2.get_next_page.return_value = None

            # Set up pagination
            mock_transactions_page1.get_next_page.side_effect = [
                mock_transactions_page2,
                None,
            ]

            mock_venmo_client.user.get_user_transactions.return_value = (
                mock_transactions_page1
            )

            # Call the function
            refresh_venmo()

            # Verify bulk_upsert was called with both transactions
            mock_bulk_upsert.assert_called_once()
            call_args = mock_bulk_upsert.call_args
            transactions = call_args[0][1]
            assert len(transactions) == 2

    def test_refresh_venmo_profile_failure(self, flask_app, mocker):
        """Test refresh_venmo function - profile retrieval failure"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = None
            mocker.patch(
                "resources.venmo.get_venmo_client", return_value=mock_venmo_client
            )

            # Call the function and expect exception
            with pytest.raises(Exception, match="Failed to get Venmo profile"):
                refresh_venmo()

    def test_venmo_to_line_items_success(
        self, flask_app, mock_venmo_transaction, mocker
    ):
        """Test venmo_to_line_items function - success case"""
        with flask_app.app_context():
            # Insert test transaction data
            test_transaction = mock_venmo_transaction
            upsert_with_id(
                venmo_raw_data_collection, test_transaction, test_transaction["id"]
            )

            mock_bulk_upsert = mocker.patch("resources.venmo.bulk_upsert")

            # Call the function
            venmo_to_line_items()

            # Verify bulk_upsert was called with line items
            mock_bulk_upsert.assert_called_once()
            call_args = mock_bulk_upsert.call_args
            assert call_args[0][0] == line_items_collection

            # Check that line items were created correctly
            line_items = call_args[0][1]
            assert len(line_items) == 1

            line_item = line_items[0]
            assert line_item.id == "line_item_venmo_txn_123"
            assert line_item.responsible_party == "John"
            assert line_item.payment_method == "Venmo"
            assert line_item.description == "Test payment"
            assert line_item.amount == 25.0

    def test_venmo_to_line_items_charge_transaction(
        self, flask_app, mock_venmo_transaction_charge, mocker
    ):
        """Test venmo_to_line_items function - charge transaction"""
        with flask_app.app_context():
            # Insert test transaction data
            test_transaction = mock_venmo_transaction_charge
            upsert_with_id(
                venmo_raw_data_collection, test_transaction, test_transaction["id"]
            )

            mock_bulk_upsert = mocker.patch("resources.venmo.bulk_upsert")

            # Call the function
            venmo_to_line_items()

            # Verify line item was created correctly for charge
            mock_bulk_upsert.assert_called_once()
            call_args = mock_bulk_upsert.call_args
            line_items = call_args[0][1]
            assert len(line_items) == 1

            line_item = line_items[0]
            assert line_item.id == "line_item_venmo_txn_456"
            assert line_item.responsible_party == "Jane"
            assert line_item.payment_method == "Venmo"
            assert line_item.description == "Test charge"
            assert line_item.amount == 15.0

    def test_venmo_to_line_items_received_transaction(
        self, flask_app, mock_venmo_transaction_received, mocker
    ):
        """Test venmo_to_line_items function - received transaction"""
        with flask_app.app_context():
            # Insert test transaction data
            test_transaction = mock_venmo_transaction_received
            upsert_with_id(
                venmo_raw_data_collection, test_transaction, test_transaction["id"]
            )

            mock_bulk_upsert = mocker.patch("resources.venmo.bulk_upsert")

            # Call the function
            venmo_to_line_items()

            # Verify line item was created correctly for received payment
            mock_bulk_upsert.assert_called_once()
            call_args = mock_bulk_upsert.call_args
            line_items = call_args[0][1]
            assert len(line_items) == 1

            line_item = line_items[0]
            assert line_item.id == "line_item_venmo_txn_789"
            assert line_item.responsible_party == "Bob"
            assert line_item.payment_method == "Venmo"
            assert line_item.description == "Test received payment"
            assert line_item.amount == -10.0  # Flipped amount

    def test_venmo_to_line_items_no_transactions(self, flask_app, mocker):
        """Test venmo_to_line_items function - no transactions to process"""
        with flask_app.app_context():
            mock_bulk_upsert = mocker.patch("resources.venmo.bulk_upsert")

            # Call the function with no transactions
            venmo_to_line_items()

            # Verify bulk_upsert was not called
            mock_bulk_upsert.assert_not_called()

    def test_venmo_to_line_items_multiple_transactions(self, flask_app, mocker):
        """Test venmo_to_line_items function - multiple transactions"""
        with flask_app.app_context():
            # Insert multiple test transactions
            transactions = [
                {
                    "id": "venmo_txn_1",
                    "_id": "venmo_txn_1",
                    "date_created": 1673778600.0,
                    "actor": {"first_name": "Neeraj"},
                    "target": {"first_name": "John"},
                    "payment_type": "pay",
                    "note": "Payment 1",
                    "amount": 25.0,
                },
                {
                    "id": "venmo_txn_2",
                    "_id": "venmo_txn_2",
                    "date_created": 1673778601.0,
                    "actor": {"first_name": "Jane"},
                    "target": {"first_name": "Neeraj"},
                    "payment_type": "charge",
                    "note": "Charge 1",
                    "amount": 15.0,
                },
                {
                    "id": "venmo_txn_3",
                    "_id": "venmo_txn_3",
                    "date_created": 1673778602.0,
                    "actor": {"first_name": "Bob"},
                    "target": {"first_name": "Neeraj"},
                    "payment_type": "pay",
                    "note": "Received payment",
                    "amount": 10.0,
                },
            ]

            for transaction in transactions:
                upsert_with_id(
                    venmo_raw_data_collection, transaction, transaction["id"]
                )

            mock_bulk_upsert = mocker.patch("resources.venmo.bulk_upsert")

            # Call the function
            venmo_to_line_items()

            # Verify bulk_upsert was called with all line items
            mock_bulk_upsert.assert_called_once()
            call_args = mock_bulk_upsert.call_args
            line_items = call_args[0][1]
            assert len(line_items) == 3

            # Check each line item
            line_item_ids = [item.id for item in line_items]
            assert "line_item_venmo_txn_1" in line_item_ids
            assert "line_item_venmo_txn_2" in line_item_ids
            assert "line_item_venmo_txn_3" in line_item_ids

            # Check amounts (received payment should be flipped)
            amounts = [item.amount for item in line_items]
            assert 25.0 in amounts  # Payment
            assert 15.0 in amounts  # Charge
            assert -10.0 in amounts  # Received (flipped)


class TestVenmoDualWrite:
    """Test dual-write functionality for Venmo endpoints"""

    def test_refresh_venmo_calls_dual_write_for_transactions(
        self, flask_app, mock_venmo_user, mocker
    ):
        """Test that refresh_venmo uses dual_write_operation for transactions"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch(
                "resources.venmo.get_venmo_client", return_value=mock_venmo_client
            )

            # Mock transaction
            mock_transaction = mocker.Mock()
            mock_transaction.date_created = 1673778600.0
            mock_transaction.actor.first_name = "Neeraj"
            mock_transaction.target.first_name = "John"
            mock_transaction.payment_type = "pay"
            mock_transaction.note = "Test payment"
            mock_transaction.amount = 25.0

            mock_transactions = mocker.Mock()
            mock_transactions.__iter__ = lambda self: iter([mock_transaction])
            mock_transactions.get_next_page.return_value = None
            mock_venmo_client.user.get_user_transactions.return_value = (
                mock_transactions
            )

            # Mock dual_write_operation
            mock_dual_write = mocker.patch("resources.venmo.dual_write_operation")
            mock_dual_write.return_value = {
                "success": True,
                "mongo_success": True,
                "pg_success": True,
            }

            # Call refresh_venmo
            refresh_venmo()

            # Verify dual_write_operation was called
            mock_dual_write.assert_called_once()
            call_kwargs = mock_dual_write.call_args[1]

            # Verify operation name
            assert call_kwargs["operation_name"] == "venmo_refresh_transactions"

            # Verify mongo_write_func and pg_write_func are callables
            assert callable(call_kwargs["mongo_write_func"])
            assert callable(call_kwargs["pg_write_func"])

    def test_venmo_to_line_items_calls_dual_write(
        self, flask_app, mock_venmo_transaction, mocker
    ):
        """Test that venmo_to_line_items uses dual_write_operation"""
        with flask_app.app_context():
            # Insert test transaction data
            test_transaction = mock_venmo_transaction
            upsert_with_id(
                venmo_raw_data_collection, test_transaction, test_transaction["id"]
            )

            # Mock dual_write_operation
            mock_dual_write = mocker.patch("resources.venmo.dual_write_operation")
            mock_dual_write.return_value = {
                "success": True,
                "mongo_success": True,
                "pg_success": True,
            }

            # Call venmo_to_line_items
            venmo_to_line_items()

            # Verify dual_write_operation was called
            mock_dual_write.assert_called_once()
            call_kwargs = mock_dual_write.call_args[1]

            # Verify operation name
            assert call_kwargs["operation_name"] == "venmo_create_line_items"

            # Verify both write functions are callables
            assert callable(call_kwargs["mongo_write_func"])
            assert callable(call_kwargs["pg_write_func"])

    def test_venmo_dual_write_mongo_failure_propagates(
        self, flask_app, mock_venmo_user, mocker
    ):
        """Test that MongoDB failure in dual-write raises exception"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch(
                "resources.venmo.get_venmo_client", return_value=mock_venmo_client
            )

            # Mock transaction
            mock_transaction = mocker.Mock()
            mock_transaction.date_created = 1673778600.0
            mock_transaction.actor.first_name = "Neeraj"
            mock_transaction.target.first_name = "John"
            mock_transaction.payment_type = "pay"
            mock_transaction.note = "Test payment"
            mock_transaction.amount = 25.0

            mock_transactions = mocker.Mock()
            mock_transactions.__iter__ = lambda self: iter([mock_transaction])
            mock_transactions.get_next_page.return_value = None
            mock_venmo_client.user.get_user_transactions.return_value = (
                mock_transactions
            )

            # Mock dual_write_operation to simulate MongoDB failure
            from utils.dual_write import DualWriteError

            mock_dual_write = mocker.patch("resources.venmo.dual_write_operation")
            mock_dual_write.side_effect = DualWriteError("MongoDB write failed")

            # Call refresh_venmo and expect exception
            with pytest.raises(DualWriteError):
                refresh_venmo()

    def test_venmo_dual_write_pg_failure_continues(
        self, flask_app, mock_venmo_user, mocker
    ):
        """Test that PostgreSQL failure in dual-write logs but continues"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch(
                "resources.venmo.get_venmo_client", return_value=mock_venmo_client
            )

            # Mock transaction
            mock_transaction = mocker.Mock()
            mock_transaction.date_created = 1673778600.0
            mock_transaction.actor.first_name = "Neeraj"
            mock_transaction.target.first_name = "John"
            mock_transaction.payment_type = "pay"
            mock_transaction.note = "Test payment"
            mock_transaction.amount = 25.0

            mock_transactions = mocker.Mock()
            mock_transactions.__iter__ = lambda self: iter([mock_transaction])
            mock_transactions.get_next_page.return_value = None
            mock_venmo_client.user.get_user_transactions.return_value = (
                mock_transactions
            )

            # Mock dual_write_operation to simulate PG failure (non-critical)
            mock_dual_write = mocker.patch("resources.venmo.dual_write_operation")
            mock_dual_write.return_value = {
                "success": True,  # Still success because MongoDB succeeded
                "mongo_success": True,
                "pg_success": False,
                "pg_error": "PostgreSQL connection failed",
            }

            # Call refresh_venmo - should not raise
            refresh_venmo()  # Should complete without exception

            # Verify dual_write was called
            mock_dual_write.assert_called_once()


class TestVenmoIntegration:
    def test_full_refresh_workflow(self, flask_app, mock_venmo_user, mocker):
        """Test the complete refresh workflow from API to database"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch(
                "resources.venmo.get_venmo_client", return_value=mock_venmo_client
            )

            # Use a Mock for the transaction for refresh_venmo
            mock_transaction = mocker.Mock()
            mock_transaction.date_created = 1673778600.0
            mock_transaction.actor.first_name = "Neeraj"
            mock_transaction.target.first_name = "John"
            mock_transaction.payment_type = "pay"
            mock_transaction.note = "Integration test payment"
            mock_transaction.amount = 25.0
            mock_transaction._id = "venmo_txn_integration"
            mock_transaction.id = "venmo_txn_integration"

            mock_transactions = mocker.Mock()
            mock_transactions.__iter__ = lambda self: iter([mock_transaction])
            mock_transactions.get_next_page.return_value = None
            mock_venmo_client.user.get_user_transactions.return_value = (
                mock_transactions
            )

            # Call refresh function (this will store a Mock in the DB, which we don't want for the next step)
            refresh_venmo()

            # Remove the Mock and insert a real dict for venmo_to_line_items
            coll = get_collection(venmo_raw_data_collection)
            coll.delete_many({})
            transaction_dict = {
                "id": "venmo_txn_integration",
                "_id": "venmo_txn_integration",
                "date_created": 1673778600.0,
                "actor": {"first_name": "Neeraj"},
                "target": {"first_name": "John"},
                "payment_type": "pay",
                "note": "Integration test payment",
                "amount": 25.0,
            }
            coll.insert_one(transaction_dict)

            # Now call line items conversion with the stored data
            mock_bulk_upsert = mocker.patch("resources.venmo.bulk_upsert")
            venmo_to_line_items()

            # Verify bulk_upsert was called for line items
            mock_bulk_upsert.assert_called_once()
            call_args = mock_bulk_upsert.call_args
            assert call_args[0][0] == line_items_collection

            line_items = call_args[0][1]
            assert len(line_items) == 1
            assert line_items[0].description == "Integration test payment"
            assert line_items[0].payment_method == "Venmo"
            assert line_items[0].amount == 25.0

    def test_venmo_edge_cases(self, flask_app, mock_venmo_user, mocker):
        """Test various edge cases in Venmo processing"""
        with flask_app.app_context():
            # Mock the get_venmo_client function
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_user
            mocker.patch(
                "resources.venmo.get_venmo_client", return_value=mock_venmo_client
            )

            # Mock bulk_upsert
            mock_bulk_upsert = mocker.patch("resources.venmo.bulk_upsert")

            # Mock edge case transactions
            mock_transactions = mocker.Mock()

            # Transaction with empty note
            mock_transaction1 = mocker.Mock()
            mock_transaction1.date_created = 1673778600.0
            mock_transaction1.actor.first_name = "Neeraj"
            mock_transaction1.target.first_name = "John"
            mock_transaction1.payment_type = "pay"
            mock_transaction1.note = ""
            mock_transaction1.amount = 0.0

            # Transaction with zero amount
            mock_transaction2 = mocker.Mock()
            mock_transaction2.date_created = 1673778601.0
            mock_transaction2.actor.first_name = "Jane"
            mock_transaction2.target.first_name = "Neeraj"
            mock_transaction2.payment_type = "charge"
            mock_transaction2.note = "Zero amount"
            mock_transaction2.amount = 0.0

            mock_transactions.__iter__ = lambda self: iter(
                [mock_transaction1, mock_transaction2]
            )
            mock_transactions.get_next_page.return_value = None

            mock_venmo_client.user.get_user_transactions.return_value = (
                mock_transactions
            )

            # Call the function
            refresh_venmo()

            # Verify transactions were processed
            mock_bulk_upsert.assert_called_once()
            call_args = mock_bulk_upsert.call_args
            transactions = call_args[0][1]
            assert len(transactions) == 2
