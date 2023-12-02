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
def expected_line_item(mock_cash_raw_data):
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

    # Ensure that the status code is 200 (OK)
    assert response.status_code == 200

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
