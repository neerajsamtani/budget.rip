import pytest


@pytest.fixture
def sample_tags(pg_session):
    """Create sample tags for testing"""
    from models.sql_models import Tag

    user_id = "user_id"
    tags_data = [
        {"id": "tag_1", "user_id": user_id, "name": "vacation"},
        {"id": "tag_2", "user_id": user_id, "name": "groceries"},
        {"id": "tag_3", "user_id": user_id, "name": "birthday"},
    ]

    tags = [Tag(**tag_data) for tag_data in tags_data]
    pg_session.add_all(tags)
    pg_session.commit()

    return tags_data


class TestTagsAPI:
    def test_tags_are_returned_sorted_alphabetically(self, test_client, jwt_token, sample_tags):
        """Tags endpoint returns all tags sorted alphabetically by name"""
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

    def test_empty_database_returns_empty_tags_list(self, test_client, jwt_token):
        """Tags endpoint returns empty array when no tags exist"""
        response = test_client.get("/api/tags", headers={"Authorization": f"Bearer {jwt_token}"})

        assert response.status_code == 200
        data = response.get_json()

        assert "data" in data
        assert data["data"] == []

    def test_tags_endpoint_requires_authentication(self, test_client):
        """Tags endpoint requires JWT authentication"""
        response = test_client.get("/api/tags")

        assert response.status_code == 401

    def test_tags_from_other_users_are_not_returned(self, test_client, flask_app, pg_session, sample_tags):
        """Tags belonging to a different user are not visible"""
        from flask_jwt_extended import create_access_token

        from models.sql_models import Tag, User

        other_user = User(
            id="user_other",
            first_name="Other",
            last_name="User",
            email="other@example.com",
            password_hash="hashed",
        )
        pg_session.add(other_user)
        pg_session.flush()
        pg_session.add(Tag(id="tag_other", user_id="user_other", name="secret"))
        pg_session.commit()

        with flask_app.app_context():
            other_token = create_access_token(identity="user_other")

        response = test_client.get("/api/tags", headers={"Authorization": f"Bearer {other_token}"})
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "secret"
