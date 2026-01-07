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
        1234567890,
        "John Doe",
        "Cash",
        "Test transaction",
        100,
    )


def test_cash_transaction_is_stored_in_database(test_client, jwt_token, flask_app):
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


def test_decimal_amounts_are_preserved(test_client, jwt_token, flask_app):
    """Decimal amounts are preserved when creating cash transactions"""
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


def test_cash_transactions_convert_to_line_items(flask_app, mock_cash_raw_data, expected_line_item):
    with flask_app.app_context():
        upsert_with_id(cash_raw_data_collection, mock_cash_raw_data, mock_cash_raw_data["id"])

        # Call the cash_to_line_items function
        cash_to_line_items()

        # Ensure that the DB state is as expected
        line_items_db = get_all_data(line_items_collection)
        assert len(line_items_db) == 1
        item_in_db = line_items_db[0]
        assert item_in_db["id"].startswith("li_")
        assert item_in_db["date"] == expected_line_item.date
        assert item_in_db["responsible_party"] == expected_line_item.responsible_party
        assert item_in_db["description"] == expected_line_item.description
        assert item_in_db["amount"] == expected_line_item.amount


def test_delete_cash_transaction_succeeds(
    test_client, jwt_token, flask_app, create_line_item_via_cash
):
    """Cash transaction can be deleted when not assigned to an event"""
    # Create a cash transaction
    create_line_item_via_cash(
        date="2023-09-15",
        person="John Doe",
        description="Test transaction to delete",
        amount=50.0,
    )

    # Get the line item ID
    with flask_app.app_context():
        line_items_db = get_all_data(line_items_collection)
        assert len(line_items_db) == 1
        line_item_id = line_items_db[0]["id"]

    # Delete the cash transaction
    response = test_client.delete(
        f"/api/cash_transaction/{line_item_id}",
        headers={"Authorization": f"Bearer {jwt_token}"},
    )

    assert response.status_code == 200
    assert response.get_json() == {"message": "Deleted cash transaction"}

    # Verify line item is deleted
    with flask_app.app_context():
        line_items_db = get_all_data(line_items_collection)
        assert len(line_items_db) == 0

        # Verify transaction is also deleted
        cash_db = get_all_data(cash_raw_data_collection)
        assert len(cash_db) == 0


def test_delete_cash_transaction_fails_when_assigned_to_event(
    test_client, jwt_token, flask_app, create_line_item_via_cash, create_event_via_api
):
    """Cash transaction cannot be deleted when assigned to an event"""
    # Create a cash transaction
    create_line_item_via_cash(
        date="2023-09-15",
        person="John Doe",
        description="Test transaction",
        amount=50.0,
    )

    # Get the line item ID
    with flask_app.app_context():
        line_items_db = get_all_data(line_items_collection)
        assert len(line_items_db) == 1
        line_item_id = line_items_db[0]["id"]

    # Create an event with this line item
    event_data = {
        "date": "2023-09-15",
        "description": "Test Event",
        "category": "Dining",
        "line_items": [line_item_id],
    }
    create_event_via_api(event_data)

    # Try to delete the cash transaction
    response = test_client.delete(
        f"/api/cash_transaction/{line_item_id}",
        headers={"Authorization": f"Bearer {jwt_token}"},
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Cannot delete: line item is assigned to an event"}

    # Verify line item still exists
    with flask_app.app_context():
        line_items_db = get_all_data(line_items_collection)
        assert len(line_items_db) == 1


def test_delete_nonexistent_line_item_returns_404(test_client, jwt_token):
    """Deleting a non-existent line item returns 404"""
    response = test_client.delete(
        "/api/cash_transaction/li_nonexistent123",
        headers={"Authorization": f"Bearer {jwt_token}"},
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Line item not found"}
