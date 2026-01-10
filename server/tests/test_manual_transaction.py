from datetime import UTC, datetime
from decimal import Decimal

import pytest

from dao import (
    create_manual_transaction,
    delete_manual_transaction,
    get_all_line_items,
    get_payment_method_by_id,
    get_transactions,
)
from helpers import html_date_to_posix
from utils.id_generator import generate_id


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
        manual_db = get_transactions("manual", None)
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
        line_items_db = get_all_line_items(None)
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
        line_items_db = get_all_line_items(None)
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
        manual_db = get_transactions("manual", None)
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
        line_items_db = get_all_line_items(None)
        assert len(line_items_db) == 1

    # Delete it
    delete_response = test_client.delete(
        f"/api/manual_transaction/{transaction_id}",
        headers={"Authorization": "Bearer " + jwt_token},
    )

    assert delete_response.status_code == 204

    # Verify it's gone
    with flask_app.app_context():
        line_items_db = get_all_line_items(None)
        assert len(line_items_db) == 0
        manual_db = get_transactions("manual", None)
        assert len(manual_db) == 0


def test_cannot_delete_nonexistent_transaction(test_client, jwt_token):
    """Deleting a nonexistent transaction returns 404"""
    response = test_client.delete(
        "/api/manual_transaction/txn_nonexistent",
        headers={"Authorization": "Bearer " + jwt_token},
    )

    assert response.status_code == 404


def test_cannot_delete_transaction_assigned_to_event(test_client, jwt_token, flask_app):
    """Cannot delete a manual transaction if its line items are assigned to an event"""
    # Create a manual transaction
    mock_request_data = {
        "date": "2023-09-15",
        "person": "John Doe",
        "description": "Assigned to event",
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

    # Get the line item ID
    with flask_app.app_context():
        line_items_db = get_all_line_items(None)
        assert len(line_items_db) == 1
        line_item_id = line_items_db[0]["id"]

    # Create an event with this line item
    event_response = test_client.post(
        "/api/events",
        json={
            "name": "Test Event",
            "category": "Food",
            "line_items": [line_item_id],
        },
        headers={"Authorization": "Bearer " + jwt_token},
    )
    assert event_response.status_code == 201

    # Try to delete the transaction - should fail
    delete_response = test_client.delete(
        f"/api/manual_transaction/{transaction_id}",
        headers={"Authorization": "Bearer " + jwt_token},
    )

    assert delete_response.status_code == 400
    assert delete_response.get_json()["error"] == (
        "Cannot delete transaction with line item assigned to an event. Remove the line item from the event first."
    )

    # Verify the transaction still exists
    with flask_app.app_context():
        line_items_db = get_all_line_items(None)
        assert len(line_items_db) == 1


# DAO Function Tests


def test_create_manual_transaction_creates_transaction_and_line_item(flask_app):
    """create_manual_transaction creates both a transaction and line item in the database"""
    with flask_app.app_context():
        transaction_id = generate_id("txn")
        line_item_id = generate_id("li")
        transaction_date = datetime.fromtimestamp(1694736000, UTC)

        create_manual_transaction(
            transaction_id=transaction_id,
            line_item_id=line_item_id,
            transaction_date=transaction_date,
            posix_date=1694736000,
            amount=Decimal("50.00"),
            description="DAO test transaction",
            payment_method_id="pm_cash",
            responsible_party="Test Person",
        )

        # Verify transaction was stored
        manual_db = get_transactions("manual", None)
        assert len(manual_db) == 1
        assert manual_db[0]["description"] == "DAO test transaction"
        assert manual_db[0]["amount"] == 50.0

        # Verify line item was stored
        line_items_db = get_all_line_items(None)
        assert len(line_items_db) == 1
        assert line_items_db[0]["id"] == line_item_id
        assert line_items_db[0]["description"] == "DAO test transaction"
        assert line_items_db[0]["responsible_party"] == "Test Person"


def test_delete_manual_transaction_removes_transaction_and_line_item(flask_app):
    """delete_manual_transaction removes both the transaction and its line item"""
    with flask_app.app_context():
        transaction_id = generate_id("txn")
        line_item_id = generate_id("li")
        transaction_date = datetime.fromtimestamp(1694736000, UTC)

        create_manual_transaction(
            transaction_id=transaction_id,
            line_item_id=line_item_id,
            transaction_date=transaction_date,
            posix_date=1694736000,
            amount=Decimal("75.00"),
            description="To be deleted",
            payment_method_id="pm_cash",
            responsible_party="Delete Test",
        )

        # Verify it exists
        assert len(get_transactions("manual", None)) == 1
        assert len(get_all_line_items(None)) == 1

        # Delete it
        result = delete_manual_transaction(transaction_id)
        assert result is True

        # Verify it's gone
        assert len(get_transactions("manual", None)) == 0
        assert len(get_all_line_items(None)) == 0


def test_delete_manual_transaction_returns_false_for_nonexistent(flask_app):
    """delete_manual_transaction returns False when transaction doesn't exist"""
    with flask_app.app_context():
        result = delete_manual_transaction("txn_nonexistent")
        assert result is False


def test_delete_manual_transaction_raises_for_assigned_line_item(flask_app, test_client, jwt_token):
    """delete_manual_transaction raises ValueError when line item is assigned to an event"""
    with flask_app.app_context():
        transaction_id = generate_id("txn")
        line_item_id = generate_id("li")
        transaction_date = datetime.fromtimestamp(1694736000, UTC)

        create_manual_transaction(
            transaction_id=transaction_id,
            line_item_id=line_item_id,
            transaction_date=transaction_date,
            posix_date=1694736000,
            amount=Decimal("100.00"),
            description="Assigned to event",
            payment_method_id="pm_cash",
            responsible_party="Event Test",
        )

    # Create an event with this line item (via API since event creation is complex)
    event_response = test_client.post(
        "/api/events",
        json={
            "name": "Test Event",
            "category": "Food",
            "line_items": [line_item_id],
        },
        headers={"Authorization": "Bearer " + jwt_token},
    )
    assert event_response.status_code == 201

    # Try to delete - should raise ValueError
    with flask_app.app_context():
        with pytest.raises(ValueError, match="assigned to an event"):
            delete_manual_transaction(transaction_id)


def test_get_payment_method_by_id_returns_payment_method(flask_app):
    """get_payment_method_by_id returns the payment method details"""
    with flask_app.app_context():
        result = get_payment_method_by_id("pm_cash")
        assert result is not None
        assert result["id"] == "pm_cash"
        assert result["name"] == "Cash"


def test_get_payment_method_by_id_returns_none_for_nonexistent(flask_app):
    """get_payment_method_by_id returns None for non-existent payment method"""
    with flask_app.app_context():
        result = get_payment_method_by_id("pm_nonexistent")
        assert result is None
