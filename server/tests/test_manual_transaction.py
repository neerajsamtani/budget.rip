from dao import (
    get_all_data,
    line_items_collection,
    manual_raw_data_collection,
)
from helpers import html_date_to_posix


def test_manual_transaction_is_stored_in_database(test_client, jwt_token, flask_app):
    """Manual transactions are stored in the database with the correct payment method"""
    mock_request_data = {
        "date": "2023-09-15",
        "person": "John Doe",
        "description": "Test transaction",
        "amount": 100,
        "payment_method_id": "pm_cash",
    }

    response = test_client.post(
        "/api/manual_transaction",
        json=mock_request_data,
        headers={"Authorization": "Bearer " + jwt_token},
    )

    assert response.status_code == 201
    response_data = response.get_json()
    assert response_data["message"] == "Created Manual Transaction"
    assert "transaction_id" in response_data

    # Verify transaction was stored
    with flask_app.app_context():
        manual_db = get_all_data(manual_raw_data_collection)
        assert len(manual_db) == 1
        item_in_db = manual_db[0]
        assert item_in_db["date"] == html_date_to_posix(mock_request_data["date"])
        assert item_in_db["person"] == mock_request_data["person"]
        assert item_in_db["description"] == mock_request_data["description"]
        assert item_in_db["amount"] == mock_request_data["amount"]


def test_manual_transaction_creates_line_item(test_client, jwt_token, flask_app):
    """Manual transactions create corresponding line items"""
    mock_request_data = {
        "date": "2023-09-15",
        "person": "John Doe",
        "description": "Test transaction",
        "amount": 100,
        "payment_method_id": "pm_cash",
    }

    response = test_client.post(
        "/api/manual_transaction",
        json=mock_request_data,
        headers={"Authorization": "Bearer " + jwt_token},
    )

    assert response.status_code == 201

    # Verify line item was created
    with flask_app.app_context():
        line_items_db = get_all_data(line_items_collection)
        assert len(line_items_db) == 1
        item_in_db = line_items_db[0]
        assert item_in_db["id"].startswith("li_")
        assert item_in_db["responsible_party"] == mock_request_data["person"]
        assert item_in_db["description"] == mock_request_data["description"]
        assert item_in_db["amount"] == mock_request_data["amount"]
        assert item_in_db["payment_method"] == "Cash"
        assert item_in_db["is_manual"] is True


def test_manual_transaction_with_venmo_payment_method(test_client, jwt_token, flask_app):
    """Manual transactions can use any payment method (e.g., Venmo)"""
    mock_request_data = {
        "date": "2023-09-15",
        "person": "Jane Smith",
        "description": "Venmo test",
        "amount": 50,
        "payment_method_id": "pm_venmo",
    }

    response = test_client.post(
        "/api/manual_transaction",
        json=mock_request_data,
        headers={"Authorization": "Bearer " + jwt_token},
    )

    assert response.status_code == 201

    with flask_app.app_context():
        line_items_db = get_all_data(line_items_collection)
        assert len(line_items_db) == 1
        item_in_db = line_items_db[0]
        assert item_in_db["payment_method"] == "Venmo"
        assert item_in_db["is_manual"] is True


def test_decimal_amounts_are_preserved(test_client, jwt_token, flask_app):
    """Decimal amounts are preserved when creating manual transactions"""
    mock_request_data = {
        "date": "2023-09-15",
        "person": "John Doe",
        "description": "Decimal transaction",
        "amount": "-110.50",  # String with decimal
        "payment_method_id": "pm_cash",
    }

    response = test_client.post(
        "/api/manual_transaction",
        json=mock_request_data,
        headers={"Authorization": "Bearer " + jwt_token},
    )

    assert response.status_code == 201

    with flask_app.app_context():
        manual_db = get_all_data(manual_raw_data_collection)
        assert len(manual_db) == 1
        item_in_db = manual_db[0]
        assert item_in_db["amount"] == -110.5  # Decimal preserved


def test_manual_transaction_requires_payment_method_id(test_client, jwt_token):
    """Manual transactions fail without payment_method_id"""
    mock_request_data = {
        "date": "2023-09-15",
        "person": "John Doe",
        "description": "Missing payment method",
        "amount": 100,
        # Missing payment_method_id
    }

    response = test_client.post(
        "/api/manual_transaction",
        json=mock_request_data,
        headers={"Authorization": "Bearer " + jwt_token},
    )

    assert response.status_code == 400
    assert "payment_method_id" in response.get_json()["error"]


def test_manual_transaction_fails_with_invalid_payment_method(test_client, jwt_token):
    """Manual transactions fail with non-existent payment method"""
    mock_request_data = {
        "date": "2023-09-15",
        "person": "John Doe",
        "description": "Invalid payment method",
        "amount": 100,
        "payment_method_id": "pm_nonexistent",
    }

    response = test_client.post(
        "/api/manual_transaction",
        json=mock_request_data,
        headers={"Authorization": "Bearer " + jwt_token},
    )

    assert response.status_code == 400
    assert "not found" in response.get_json()["error"]


def test_delete_manual_transaction(test_client, jwt_token, flask_app):
    """Manual transactions can be deleted"""
    # First create a manual transaction
    mock_request_data = {
        "date": "2023-09-15",
        "person": "John Doe",
        "description": "To be deleted",
        "amount": 100,
        "payment_method_id": "pm_cash",
    }

    create_response = test_client.post(
        "/api/manual_transaction",
        json=mock_request_data,
        headers={"Authorization": "Bearer " + jwt_token},
    )

    assert create_response.status_code == 201
    transaction_id = create_response.get_json()["transaction_id"]

    # Verify it exists
    with flask_app.app_context():
        line_items_db = get_all_data(line_items_collection)
        assert len(line_items_db) == 1

    # Delete it
    delete_response = test_client.delete(
        f"/api/manual_transaction/{transaction_id}",
        headers={"Authorization": "Bearer " + jwt_token},
    )

    assert delete_response.status_code == 204

    # Verify it's gone
    with flask_app.app_context():
        line_items_db = get_all_data(line_items_collection)
        assert len(line_items_db) == 0
        manual_db = get_all_data(manual_raw_data_collection)
        assert len(manual_db) == 0


def test_cannot_delete_nonexistent_transaction(test_client, jwt_token):
    """Deleting a nonexistent transaction returns 404"""
    response = test_client.delete(
        "/api/manual_transaction/txn_nonexistent",
        headers={"Authorization": "Bearer " + jwt_token},
    )

    assert response.status_code == 404
