import pytest


@pytest.fixture
def sample_tags(pg_session):
    """Create sample tags for testing"""
    from models.sql_models import Tag

    tags_data = [
        {"id": "tag_1", "name": "vacation"},
        {"id": "tag_2", "name": "groceries"},
        {"id": "tag_3", "name": "birthday"},
    ]

    tags = [Tag(**tag_data) for tag_data in tags_data]
    pg_session.add_all(tags)
    pg_session.commit()

    return tags_data


class TestTagsAPI:
    def test_get_all_tags_success(self, test_client, jwt_token, sample_tags):
        """Test GET /api/tags returns all tags ordered by name"""
        response = test_client.get("/api/tags", headers={"Authorization": f"Bearer {jwt_token}"})

        assert response.status_code == 200
        data = response.get_json()

        assert "data" in data
        assert len(data["data"]) == 3

        # Verify tags are ordered by name
        tag_names = [tag["name"] for tag in data["data"]]
        assert tag_names == ["birthday", "groceries", "vacation"]

        # Verify each tag has id and name
        for tag in data["data"]:
            assert "id" in tag
            assert "name" in tag

    def test_get_all_tags_empty(self, test_client, jwt_token):
        """Test GET /api/tags returns empty array when no tags exist"""
        response = test_client.get("/api/tags", headers={"Authorization": f"Bearer {jwt_token}"})

        assert response.status_code == 200
        data = response.get_json()

        assert "data" in data
        assert data["data"] == []

    def test_get_all_tags_requires_authentication(self, test_client):
        """Test GET /api/tags requires JWT authentication"""
        response = test_client.get("/api/tags")

        assert response.status_code == 401

    def test_get_all_tags_handles_database_error(self, test_client, jwt_token, mocker):
        """Test GET /api/tags handles database errors gracefully"""
        # Mock get_all_tags to raise an exception
        mocker.patch("resources.tags.get_all_tags", side_effect=Exception("Database error"))

        response = test_client.get("/api/tags", headers={"Authorization": f"Bearer {jwt_token}"})

        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
