"""Tests for the Category API endpoints."""

from datetime import UTC, datetime

from models.sql_models import (
    Category,
    Event,
    EventLineItem,
    LineItem,
    PaymentMethod,
    Transaction,
)
from utils.id_generator import generate_id


class TestCategoryAPI:
    """Tests for category CRUD operations."""

    def test_get_all_categories(self, test_client, jwt_token):
        """Test GET /api/categories returns all categories."""
        response = test_client.get(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        # Should have categories seeded by conftest
        assert len(data["data"]) > 0
        # Verify structure (no is_active field)
        for cat in data["data"]:
            assert "id" in cat
            assert "name" in cat
            assert "is_active" not in cat

    def test_get_all_categories_requires_auth(self, test_client):
        """Test GET /api/categories requires authentication."""
        response = test_client.get("/api/categories")
        assert response.status_code == 401

    def test_get_category_by_id(self, test_client, jwt_token):
        """Test GET /api/categories/<id> returns a specific category."""
        response = test_client.get(
            "/api/categories/cat_dining",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["id"] == "cat_dining"
        assert data["data"]["name"] == "Dining"

    def test_get_category_by_id_not_found(self, test_client, jwt_token):
        """Test GET /api/categories/<id> returns 404 for non-existent category."""
        response = test_client.get(
            "/api/categories/cat_nonexistent",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_create_category(self, test_client, jwt_token):
        """Test POST /api/categories creates a new category."""
        response = test_client.post(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "Utilities"}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["data"]["name"] == "Utilities"
        assert data["data"]["id"].startswith("cat_")
        assert "is_active" not in data["data"]

    def test_create_category_requires_name(self, test_client, jwt_token):
        """Test POST /api/categories requires a name."""
        response = test_client.post(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_create_category_empty_name(self, test_client, jwt_token):
        """Test POST /api/categories rejects empty name."""
        response = test_client.post(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "   "}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_create_category_duplicate_name(self, test_client, jwt_token):
        """Test POST /api/categories rejects duplicate category name."""
        # Create a new category
        response = test_client.post(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "Pets"}
        )
        assert response.status_code == 201

        # Try to create another with the same name
        response = test_client.post(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "Pets"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "already exists" in data["error"]

    def test_create_category_case_insensitive_duplicate(self, test_client, jwt_token):
        """Test POST /api/categories rejects case-insensitive duplicate names."""
        # Create a new category
        response = test_client.post(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "Insurance"}
        )
        assert response.status_code == 201

        # Try to create another with different case
        response = test_client.post(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "INSURANCE"}
        )
        assert response.status_code == 400

    def test_update_category(self, test_client, jwt_token):
        """Test PUT /api/categories/<id> updates a category."""
        # Create a category first
        create_response = test_client.post(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "OldName"}
        )
        assert create_response.status_code == 201
        category_id = create_response.get_json()["data"]["id"]

        # Update it
        response = test_client.put(
            f"/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "NewName"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["name"] == "NewName"

    def test_update_category_not_found(self, test_client, jwt_token):
        """Test PUT /api/categories/<id> returns 404 for non-existent category."""
        response = test_client.put(
            "/api/categories/cat_nonexistent",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "Test"}
        )
        assert response.status_code == 404

    def test_update_category_empty_name(self, test_client, jwt_token):
        """Test PUT /api/categories/<id> rejects empty name."""
        response = test_client.put(
            "/api/categories/cat_dining",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "   "}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "empty" in data["error"].lower()

    def test_update_category_duplicate_name(self, test_client, jwt_token):
        """Test PUT /api/categories/<id> rejects name that conflicts with another category."""
        # Try to update Dining to have the same name as Entertainment
        response = test_client.put(
            "/api/categories/cat_dining",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "Entertainment"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "already exists" in data["error"]

    def test_delete_category(self, test_client, jwt_token):
        """Test DELETE /api/categories/<id> deletes a category."""
        # Create a category first
        create_response = test_client.post(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "ToDelete"}
        )
        category_id = create_response.get_json()["data"]["id"]

        # Delete it
        response = test_client.delete(
            f"/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "deleted" in data["message"].lower()

        # Verify it's no longer in the categories list
        list_response = test_client.get(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        categories = list_response.get_json()["data"]
        assert not any(c["id"] == category_id for c in categories)

    def test_delete_category_not_found(self, test_client, jwt_token):
        """Test DELETE /api/categories/<id> returns 404 for non-existent category."""
        response = test_client.delete(
            "/api/categories/cat_nonexistent",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert response.status_code == 404

    def test_delete_category_in_use_by_event(self, test_client, jwt_token, pg_session):
        """Test DELETE /api/categories/<id> fails when category is used by an event."""
        # Create a new category via API
        create_response = test_client.post(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "InUseCategory"}
        )
        assert create_response.status_code == 201
        category_id = create_response.get_json()["data"]["id"]

        # Get the actual category from the database
        category = pg_session.query(Category).filter(Category.id == category_id).first()

        # Create supporting data for an event
        payment_method = PaymentMethod(
            id=generate_id("pm"),
            name="Test PM Delete",
            type="credit",
        )
        transaction = Transaction(
            id=generate_id("txn"),
            source="cash",
            source_id=f"cash_{generate_id('src')}",
            source_data={},
            transaction_date=datetime.now(UTC),
        )
        pg_session.add_all([payment_method, transaction])
        pg_session.commit()

        # Create a line item
        line_item = LineItem(
            id=generate_id("li"),
            transaction_id=transaction.id,
            date=datetime.now(UTC),
            amount=100.00,
            description="Test Line Item",
            payment_method_id=payment_method.id,
        )
        pg_session.add(line_item)
        pg_session.commit()

        # Create an event using this category
        event = Event(
            id=generate_id("evt"),
            date=datetime.now(UTC),
            description="Test Event",
            category_id=category.id,
        )
        pg_session.add(event)
        pg_session.commit()

        # Link line item to event
        event_line_item = EventLineItem(
            id=generate_id("eli"),
            event_id=event.id,
            line_item_id=line_item.id,
        )
        pg_session.add(event_line_item)
        pg_session.commit()

        # Try to delete the category - should fail
        response = test_client.delete(
            f"/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "in use" in data["error"].lower()

        # Verify the category still exists
        get_response = test_client.get(
            f"/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert get_response.status_code == 200


class TestCategoryIntegration:
    """Integration tests for category operations."""

    def test_categories_ordered_by_name(self, test_client, jwt_token):
        """Test GET /api/categories returns categories ordered by name."""
        response = test_client.get(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert response.status_code == 200
        categories = response.get_json()["data"]

        # Check alphabetical order
        names = [c["name"] for c in categories]
        assert names == sorted(names)

    def test_full_crud_workflow(self, test_client, jwt_token):
        """Test complete CRUD workflow for categories."""
        # Create
        create_response = test_client.post(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "Workflow Test"}
        )
        assert create_response.status_code == 201
        category_id = create_response.get_json()["data"]["id"]

        # Read
        read_response = test_client.get(
            f"/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert read_response.status_code == 200
        assert read_response.get_json()["data"]["name"] == "Workflow Test"

        # Update
        update_response = test_client.put(
            f"/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "Updated Workflow"}
        )
        assert update_response.status_code == 200
        assert update_response.get_json()["data"]["name"] == "Updated Workflow"

        # Delete
        delete_response = test_client.delete(
            f"/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert delete_response.status_code == 200

        # Verify deleted (not in list)
        list_response = test_client.get(
            "/api/categories",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        categories = list_response.get_json()["data"]
        assert not any(c["id"] == category_id for c in categories)
