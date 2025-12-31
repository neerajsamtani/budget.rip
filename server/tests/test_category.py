"""Tests for the Category API endpoints."""


class TestCategoryAPI:
    """Tests for category CRUD operations."""

    def test_get_all_categories(self, test_client, jwt_token):
        """Test GET /api/categories returns all active categories."""
        response = test_client.get("/api/categories", headers={"Authorization": f"Bearer {jwt_token}"})
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        # Should have categories seeded by conftest
        assert len(data["data"]) > 0
        # Verify structure
        for cat in data["data"]:
            assert "id" in cat
            assert "name" in cat
            assert "is_active" in cat

    def test_get_all_categories_requires_auth(self, test_client):
        """Test GET /api/categories requires authentication."""
        response = test_client.get("/api/categories")
        assert response.status_code == 401

    def test_get_category_by_id(self, test_client, jwt_token):
        """Test GET /api/categories/<id> returns a specific category."""
        response = test_client.get("/api/categories/cat_dining", headers={"Authorization": f"Bearer {jwt_token}"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["id"] == "cat_dining"
        assert data["data"]["name"] == "Dining"

    def test_get_category_by_id_not_found(self, test_client, jwt_token):
        """Test GET /api/categories/<id> returns 404 for non-existent category."""
        response = test_client.get("/api/categories/cat_nonexistent", headers={"Authorization": f"Bearer {jwt_token}"})
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_create_category(self, test_client, jwt_token):
        """Test POST /api/categories creates a new category."""
        response = test_client.post(
            "/api/categories", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "Utilities"}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["data"]["name"] == "Utilities"
        assert data["data"]["is_active"] is True
        assert data["data"]["id"].startswith("cat_")

    def test_create_category_requires_name(self, test_client, jwt_token):
        """Test POST /api/categories requires a name."""
        response = test_client.post("/api/categories", headers={"Authorization": f"Bearer {jwt_token}"}, json={})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_create_category_empty_name(self, test_client, jwt_token):
        """Test POST /api/categories rejects empty name."""
        response = test_client.post("/api/categories", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "   "})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_create_category_duplicate_name(self, test_client, jwt_token):
        """Test POST /api/categories rejects duplicate category name."""
        # Create a new category
        response = test_client.post("/api/categories", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "Pets"})
        assert response.status_code == 201

        # Try to create another with the same name
        response = test_client.post("/api/categories", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "Pets"})
        assert response.status_code == 400
        data = response.get_json()
        assert "already exists" in data["error"]

    def test_create_category_case_insensitive_duplicate(self, test_client, jwt_token):
        """Test POST /api/categories rejects case-insensitive duplicate names."""
        # Create a new category
        response = test_client.post(
            "/api/categories", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "Insurance"}
        )
        assert response.status_code == 201

        # Try to create another with different case
        response = test_client.post(
            "/api/categories", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "INSURANCE"}
        )
        assert response.status_code == 400

    def test_update_category(self, test_client, jwt_token):
        """Test PUT /api/categories/<id> updates a category."""
        # Create a category first
        create_response = test_client.post(
            "/api/categories", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "OldName"}
        )
        assert create_response.status_code == 201
        category_id = create_response.get_json()["data"]["id"]

        # Update it
        response = test_client.put(
            f"/api/categories/{category_id}", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "NewName"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["name"] == "NewName"

    def test_update_category_not_found(self, test_client, jwt_token):
        """Test PUT /api/categories/<id> returns 404 for non-existent category."""
        response = test_client.put(
            "/api/categories/cat_nonexistent", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "Test"}
        )
        assert response.status_code == 404

    def test_update_category_empty_name(self, test_client, jwt_token):
        """Test PUT /api/categories/<id> rejects empty name."""
        response = test_client.put(
            "/api/categories/cat_dining", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "   "}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "empty" in data["error"].lower()

    def test_update_category_duplicate_name(self, test_client, jwt_token):
        """Test PUT /api/categories/<id> rejects name that conflicts with another category."""
        # Try to update Dining to have the same name as Entertainment
        response = test_client.put(
            "/api/categories/cat_dining", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "Entertainment"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "already exists" in data["error"]

    def test_update_category_is_active(self, test_client, jwt_token):
        """Test PUT /api/categories/<id> can update is_active status."""
        # Create a category
        create_response = test_client.post(
            "/api/categories", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "TempCategory"}
        )
        category_id = create_response.get_json()["data"]["id"]

        # Deactivate it
        response = test_client.put(
            f"/api/categories/{category_id}", headers={"Authorization": f"Bearer {jwt_token}"}, json={"is_active": False}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["is_active"] is False

    def test_delete_category(self, test_client, jwt_token):
        """Test DELETE /api/categories/<id> soft-deletes a category."""
        # Create a category first
        create_response = test_client.post(
            "/api/categories", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "ToDelete"}
        )
        category_id = create_response.get_json()["data"]["id"]

        # Delete it
        response = test_client.delete(f"/api/categories/{category_id}", headers={"Authorization": f"Bearer {jwt_token}"})
        assert response.status_code == 200
        data = response.get_json()
        assert "deleted" in data["message"].lower()

        # Verify it's no longer in the active categories list
        list_response = test_client.get("/api/categories", headers={"Authorization": f"Bearer {jwt_token}"})
        categories = list_response.get_json()["data"]
        assert not any(c["id"] == category_id for c in categories)

    def test_delete_category_not_found(self, test_client, jwt_token):
        """Test DELETE /api/categories/<id> returns 404 for non-existent category."""
        response = test_client.delete("/api/categories/cat_nonexistent", headers={"Authorization": f"Bearer {jwt_token}"})
        assert response.status_code == 404

    def test_reactivate_soft_deleted_category(self, test_client, jwt_token):
        """Test creating a category with the same name as a soft-deleted one reactivates it."""
        # Create a category
        create_response = test_client.post(
            "/api/categories", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "Reactivate Test"}
        )
        category_id = create_response.get_json()["data"]["id"]

        # Delete it
        test_client.delete(f"/api/categories/{category_id}", headers={"Authorization": f"Bearer {jwt_token}"})

        # Create it again with same name - should reactivate
        reactivate_response = test_client.post(
            "/api/categories", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "Reactivate Test"}
        )
        assert reactivate_response.status_code == 201
        data = reactivate_response.get_json()
        assert data["data"]["is_active"] is True


class TestCategoryIntegration:
    """Integration tests for category operations."""

    def test_categories_ordered_by_name(self, test_client, jwt_token):
        """Test GET /api/categories returns categories ordered by name."""
        response = test_client.get("/api/categories", headers={"Authorization": f"Bearer {jwt_token}"})
        assert response.status_code == 200
        categories = response.get_json()["data"]

        # Check alphabetical order
        names = [c["name"] for c in categories]
        assert names == sorted(names)

    def test_full_crud_workflow(self, test_client, jwt_token):
        """Test complete CRUD workflow for categories."""
        # Create
        create_response = test_client.post(
            "/api/categories", headers={"Authorization": f"Bearer {jwt_token}"}, json={"name": "Workflow Test"}
        )
        assert create_response.status_code == 201
        category_id = create_response.get_json()["data"]["id"]

        # Read
        read_response = test_client.get(f"/api/categories/{category_id}", headers={"Authorization": f"Bearer {jwt_token}"})
        assert read_response.status_code == 200
        assert read_response.get_json()["data"]["name"] == "Workflow Test"

        # Update
        update_response = test_client.put(
            f"/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={"name": "Updated Workflow"},
        )
        assert update_response.status_code == 200
        assert update_response.get_json()["data"]["name"] == "Updated Workflow"

        # Delete
        delete_response = test_client.delete(
            f"/api/categories/{category_id}", headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert delete_response.status_code == 200

        # Verify deleted (not in active list)
        list_response = test_client.get("/api/categories", headers={"Authorization": f"Bearer {jwt_token}"})
        categories = list_response.get_json()["data"]
        assert not any(c["id"] == category_id for c in categories)
