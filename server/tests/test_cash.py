import pytest

from dao import (
    cash_raw_data_collection,
    get_all_data,
    line_items_collection,
    upsert_with_id,
)
from helpers import html_date_to_posix
from resources.cash import cash_to_line_items
from resources.line_item import LineItem


@pytest.fixture
def mock_cash_raw_data():
    return {
        "id": 1,
        "date": 1234567890,
        "person": "John Doe",
        "description": "Test transaction",
        "amount": 100,
    }


@pytest.fixture
def expected_line_item():
    return LineItem(
        "line_item_1",
        1234567890,
        "John Doe",
        "Cash",
        "Test transaction",
        100,
    )


def test_create_cash_transaction_api(test_client, jwt_token, flask_app):
    # Define a mock request with JSON data
    mock_request_data = {
        "date": "2023-09-15",
        "person": "John Doe",
        "description": "Test transaction",
        "amount": 100,
    }

    # Send a POST request to the API
    response = test_client.post(
        "/api/cash_transaction",
        json=mock_request_data,
        headers={"Authorization": "Bearer " + jwt_token},
    )

    # Ensure that the status code is 201 (Created)
    assert response.status_code == 201

    # Ensure that the JSON response is as expected
    expected_response = "Created Cash Transaction"
    assert response.get_json() == expected_response

    # Ensure that the DB state is as expected
    with flask_app.app_context():
        cash_db = get_all_data(cash_raw_data_collection)
        assert len(cash_db) == 1
        item_in_db = cash_db[0]
        assert item_in_db["date"] == html_date_to_posix(mock_request_data["date"])
        assert item_in_db["person"] == mock_request_data["person"]
        assert item_in_db["description"] == mock_request_data["description"]
        assert item_in_db["amount"] == mock_request_data["amount"]


def test_create_cash_transaction_api_decimal_amounts(test_client, jwt_token, flask_app):
    """Test that the cash transaction API handles decimal amounts correctly."""
    # Test with decimal string (common from frontend forms)
    mock_request_data = {
        "date": "2023-09-15",
        "person": "John Doe",
        "description": "Decimal transaction",
        "amount": "-110.50",  # String with decimal
    }

    # Send a POST request to the API
    response = test_client.post(
        "/api/cash_transaction",
        json=mock_request_data,
        headers={"Authorization": "Bearer " + jwt_token},
    )

    # Ensure that the status code is 201 (Created)
    assert response.status_code == 201

    # Ensure that the JSON response is as expected
    expected_response = "Created Cash Transaction"
    assert response.get_json() == expected_response

    # Ensure that the DB state is as expected with preserved decimal amount
    with flask_app.app_context():
        cash_db = get_all_data(cash_raw_data_collection)
        assert len(cash_db) == 1
        item_in_db = cash_db[0]
        assert item_in_db["date"] == html_date_to_posix(mock_request_data["date"])
        assert item_in_db["person"] == mock_request_data["person"]
        assert item_in_db["description"] == mock_request_data["description"]
        assert item_in_db["amount"] == -110.5  # Decimal preserved


def test_cash_to_line_items(flask_app, mock_cash_raw_data, expected_line_item):
    with flask_app.app_context():
        upsert_with_id(
            cash_raw_data_collection, mock_cash_raw_data, mock_cash_raw_data["id"]
        )

        # Call the cash_to_line_items function
        cash_to_line_items()

        # Ensure that the DB state is as expected
        line_items_db = get_all_data(line_items_collection)
        assert len(line_items_db) == 1
        item_in_db = line_items_db[0]
        assert item_in_db["id"] == expected_line_item.id
        assert item_in_db["date"] == expected_line_item.date
        assert item_in_db["responsible_party"] == expected_line_item.responsible_party
        assert item_in_db["description"] == expected_line_item.description
        assert item_in_db["amount"] == expected_line_item.amount

    # Ensure that upsert was called with the correct LineItem objects


class TestCashDualWrite:
    """Test dual-write functionality for Cash endpoints"""

    def test_create_cash_transaction_calls_dual_write(self, test_client, jwt_token, flask_app, mocker):
        """Test that create_cash_transaction_api uses dual_write_operation"""
        with flask_app.app_context():
            # Mock dual_write_operation
            mock_dual_write = mocker.patch("resources.cash.dual_write_operation")
            mock_dual_write.return_value = {
                "success": True,
                "mongo_success": True,
                "pg_success": True,
            }

            # Mock cash_to_line_items to prevent actual line item creation
            mocker.patch("resources.cash.cash_to_line_items")

            # Send a POST request to create cash transaction
            mock_request_data = {
                "date": "2023-09-15",
                "person": "John Doe",
                "description": "Test transaction",
                "amount": 100,
            }

            response = test_client.post(
                "/api/cash_transaction",
                json=mock_request_data,
                headers={"Authorization": "Bearer " + jwt_token},
            )

            # Ensure the request succeeded
            assert response.status_code == 201

            # Verify dual_write_operation was called
            mock_dual_write.assert_called_once()
            call_kwargs = mock_dual_write.call_args[1]

            # Verify operation name
            assert call_kwargs["operation_name"] == "cash_create_transaction"

            # Verify mongo_write_func and pg_write_func are callables
            assert callable(call_kwargs["mongo_write_func"])
            assert callable(call_kwargs["pg_write_func"])

    def test_cash_to_line_items_calls_dual_write(self, flask_app, mock_cash_raw_data, mocker):
        """Test that cash_to_line_items uses dual_write_operation"""
        with flask_app.app_context():
            # Insert test transaction data
            upsert_with_id(
                cash_raw_data_collection, mock_cash_raw_data, mock_cash_raw_data["id"]
            )

            # Mock dual_write_operation
            mock_dual_write = mocker.patch("resources.cash.dual_write_operation")
            mock_dual_write.return_value = {
                "success": True,
                "mongo_success": True,
                "pg_success": True,
            }

            # Call cash_to_line_items
            cash_to_line_items()

            # Verify dual_write_operation was called
            mock_dual_write.assert_called_once()
            call_kwargs = mock_dual_write.call_args[1]

            # Verify operation name
            assert call_kwargs["operation_name"] == "cash_create_line_items"

            # Verify both write functions are callables
            assert callable(call_kwargs["mongo_write_func"])
            assert callable(call_kwargs["pg_write_func"])

    def test_cash_dual_write_mongo_failure_propagates(self, flask_app, mocker):
        """Test that MongoDB failure in dual-write raises exception"""
        with flask_app.app_context():
            # Mock dual_write_operation to simulate MongoDB failure
            from utils.dual_write import DualWriteError
            from resources.cash import cash_to_line_items

            # Insert test transaction data first
            transaction_data = {
                "id": 1,
                "date": 1234567890,
                "person": "John Doe",
                "description": "Test transaction",
                "amount": 100,
            }
            upsert_with_id(cash_raw_data_collection, transaction_data, transaction_data["id"])

            # Mock dual_write_operation to simulate MongoDB failure
            mock_dual_write = mocker.patch("resources.cash.dual_write_operation")
            mock_dual_write.side_effect = DualWriteError("MongoDB write failed")

            # Call cash_to_line_items directly - should raise
            with pytest.raises(DualWriteError):
                cash_to_line_items()

    def test_cash_dual_write_pg_failure_continues(self, test_client, jwt_token, flask_app, mocker):
        """Test that PostgreSQL failure in dual-write logs but continues"""
        with flask_app.app_context():
            # Mock dual_write_operation to simulate PG failure (non-critical)
            mock_dual_write = mocker.patch("resources.cash.dual_write_operation")
            mock_dual_write.return_value = {
                "success": True,  # Still success because MongoDB succeeded
                "mongo_success": True,
                "pg_success": False,
                "pg_error": "PostgreSQL connection failed",
            }

            # Mock cash_to_line_items to prevent actual line item creation
            mocker.patch("resources.cash.cash_to_line_items")

            # Send a POST request to create cash transaction
            mock_request_data = {
                "date": "2023-09-15",
                "person": "John Doe",
                "description": "Test transaction",
                "amount": 100,
            }

            response = test_client.post(
                "/api/cash_transaction",
                json=mock_request_data,
                headers={"Authorization": "Bearer " + jwt_token},
            )

            # Should succeed (201) despite PG failure
            assert response.status_code == 201

            # Verify dual_write was called
            mock_dual_write.assert_called_once()
