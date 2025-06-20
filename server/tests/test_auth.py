import pytest

from constants import GATED_USERS
from dao import upsert_with_id, users_collection


@pytest.fixture
def mock_user_data():
    return {
        "id": "user_1",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password_hash": "hashed_password_123",
    }


@pytest.fixture
def mock_gated_user_data():
    return {
        "id": "user_2",
        "first_name": "Neeraj",
        "last_name": "Samtani",
        "email": "neerajjsamtani@gmail.com",  # This is in GATED_USERS
        "password_hash": "hashed_password_456",
    }


@pytest.fixture
def mock_non_gated_user_data():
    return {
        "id": "user_3",
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",  # This is NOT in GATED_USERS
        "password_hash": "hashed_password_789",
    }


class TestAuthAPI:
    def test_signup_user_api_success(self, test_client, flask_app):
        """Test POST /api/auth/signup endpoint - success case with gated user"""
        # Test API call with gated user
        signup_data = {
            "first_name": "Neeraj",
            "last_name": "Samtani",
            "email": "neerajjsamtani@gmail.com",  # This is in GATED_USERS
            "password": "testpassword123",
        }

        response = test_client.post("/api/auth/signup", json=signup_data)

        assert response.status_code == 201
        assert response.get_data(as_text=True).strip() == '"Created User"'

        # Verify user was created in database
        with flask_app.app_context():
            from dao import get_user_by_email

            created_user = get_user_by_email("neerajjsamtani@gmail.com")
            assert created_user is not None
            assert created_user["first_name"] == "Neeraj"
            assert created_user["last_name"] == "Samtani"
            assert created_user["email"] == "neerajjsamtani@gmail.com"
            assert "password_hash" in created_user  # Should have hashed password

    def test_signup_user_api_user_already_exists(self, test_client, flask_app):
        """Test POST /api/auth/signup endpoint - user already exists"""
        # Insert existing user first
        with flask_app.app_context():
            existing_user = {
                "id": "existing_user",
                "first_name": "Neeraj",
                "last_name": "Samtani",
                "email": "neerajjsamtani@gmail.com",
                "password_hash": "existing_hash",
            }
            upsert_with_id(users_collection, existing_user, existing_user["id"])

        # Test API call with same email
        signup_data = {
            "first_name": "Neeraj",
            "last_name": "Samtani",
            "email": "neerajjsamtani@gmail.com",
            "password": "testpassword123",
        }

        response = test_client.post("/api/auth/signup", json=signup_data)

        assert response.status_code == 400
        assert response.get_data(as_text=True).strip() == '"User Already Exists"'

    def test_signup_user_api_not_gated_user(self, test_client):
        """Test POST /api/auth/signup endpoint - user not in gated list"""
        # Test API call with non-gated user
        signup_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",  # This is NOT in GATED_USERS
            "password": "testpassword123",
        }

        response = test_client.post("/api/auth/signup", json=signup_data)

        assert response.status_code == 403
        assert (
            response.get_data(as_text=True).strip()
            == '"User Not Signed Up For Private Beta"'
        )

    def test_signup_user_api_missing_fields(self, test_client):
        """Test POST /api/auth/signup endpoint - missing required fields"""
        # Test with missing email
        signup_data_missing_email = {
            "first_name": "John",
            "last_name": "Doe",
            "password": "testpassword123",
        }

        response = test_client.post("/api/auth/signup", json=signup_data_missing_email)
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"].startswith("Missing required field: email")

        # Test with missing password
        signup_data_missing_password = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "neerajjsamtani@gmail.com",
        }

        response = test_client.post(
            "/api/auth/signup", json=signup_data_missing_password
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"].startswith("Missing required field: password")

    def test_login_user_api_success(self, test_client, flask_app):
        """Test POST /api/auth/login endpoint - success case"""
        # Insert test user with known password hash
        with flask_app.app_context():
            from helpers import hash_password

            test_user = {
                "id": "test_user",
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "password_hash": hash_password("testpassword123"),
            }
            upsert_with_id(users_collection, test_user, test_user["id"])

        # Test API call with correct credentials
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123",
        }

        response = test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.get_json()
        assert data["login"] is True

        # Check that JWT cookies are set
        assert "access_token_cookie" in response.headers.get("Set-Cookie", "")

    def test_login_user_api_invalid_email(self, test_client):
        """Test POST /api/auth/login endpoint - invalid email"""
        # Test API call with non-existent email
        login_data = {
            "email": "nonexistent@example.com",
            "password": "testpassword123",
        }

        response = test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "Email or password invalid"

    def test_login_user_api_invalid_password(self, test_client, flask_app):
        """Test POST /api/auth/login endpoint - invalid password"""
        # Insert test user
        with flask_app.app_context():
            from helpers import hash_password

            test_user = {
                "id": "test_user",
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "password_hash": hash_password("correctpassword"),
            }
            upsert_with_id(users_collection, test_user, test_user["id"])

        # Test API call with wrong password
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword",
        }

        response = test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "Email or password invalid"

    def test_login_user_api_missing_fields(self, test_client):
        """Test POST /api/auth/login endpoint - missing required fields"""
        # Test with missing email
        login_data_missing_email = {
            "password": "testpassword123",
        }

        response = test_client.post("/api/auth/login", json=login_data_missing_email)
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"].startswith("Missing required field: email")

        # Test with missing password
        login_data_missing_password = {
            "email": "test@example.com",
        }

        response = test_client.post("/api/auth/login", json=login_data_missing_password)
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"].startswith("Missing required field: password")

    def test_logout_api_success(self, test_client):
        """Test POST /api/auth/logout endpoint - success case"""
        response = test_client.post("/api/auth/logout")

        assert response.status_code == 200
        data = response.get_json()
        assert data["logout"] is True

        # Check that JWT cookies are unset
        set_cookie_header = response.headers.get("Set-Cookie", "")
        assert (
            "access_token_cookie=;" in set_cookie_header
            or "access_token_cookie=; " in set_cookie_header
        )


class TestAuthFunctions:
    def test_get_user_by_email_success(self, flask_app):
        """Test get_user_by_email function - success case"""
        with flask_app.app_context():
            from dao import get_user_by_email

            # Insert test user
            test_user = {
                "id": "test_user",
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "password_hash": "test_hash",
            }
            upsert_with_id(users_collection, test_user, test_user["id"])

            # Test function call
            found_user = get_user_by_email("test@example.com")

            assert found_user is not None
            assert found_user["email"] == "test@example.com"
            assert found_user["first_name"] == "Test"
            assert found_user["last_name"] == "User"

    def test_get_user_by_email_not_found(self, flask_app):
        """Test get_user_by_email function - user not found"""
        with flask_app.app_context():
            from dao import get_user_by_email

            # Test function call with non-existent email
            found_user = get_user_by_email("nonexistent@example.com")

            assert found_user is None

    def test_gated_users_constant(self):
        """Test that GATED_USERS constant is properly defined"""
        assert isinstance(GATED_USERS, list)
        assert len(GATED_USERS) > 0
        assert "neerajjsamtani@gmail.com" in GATED_USERS

    def test_password_hashing_consistency(self, flask_app):
        """Test that password hashing is consistent"""
        with flask_app.app_context():
            from helpers import check_password, hash_password

            password = "testpassword123"
            hashed = hash_password(password)

            # Should be able to check the password
            assert check_password(hashed, password) is True
            assert check_password(hashed, "wrongpassword") is False

    def test_jwt_token_creation(self, flask_app):
        """Test JWT token creation and validation"""
        with flask_app.app_context():
            from flask_jwt_extended import create_access_token, decode_token

            # Create a token
            user_id = "test_user_id"
            token = create_access_token(identity=user_id)

            # Decode the token
            decoded = decode_token(token)
            assert decoded["sub"] == user_id
