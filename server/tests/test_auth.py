import pytest

from constants import GATED_USERS


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
    def test_signup_creates_user_when_email_is_in_gated_list(self, test_client, flask_app):
        """Signup creates a new user when the email is in the gated users list"""
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

    def test_signup_fails_when_user_already_exists(self, test_client, flask_app, create_user_via_api):
        """Signup fails with 400 when user already exists"""
        # Create existing user via API
        create_user_via_api(
            {
                "first_name": "Neeraj",
                "last_name": "Samtani",
                "email": "neerajjsamtani@gmail.com",
                "password": "existingpassword",
            }
        )

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

    def test_signup_rejects_email_not_in_gated_list(self, test_client):
        """Signup rejects users whose email is not in the private beta list"""
        # Test API call with non-gated user
        signup_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",  # This is NOT in GATED_USERS
            "password": "testpassword123",
        }

        response = test_client.post("/api/auth/signup", json=signup_data)

        assert response.status_code == 403
        assert response.get_data(as_text=True).strip() == '"User Not Signed Up For Private Beta"'

    def test_signup_requires_email_and_password(self, test_client):
        """Signup fails when required fields are missing"""
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

        response = test_client.post("/api/auth/signup", json=signup_data_missing_password)
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"].startswith("Missing required field: password")

    def test_login_sets_jwt_cookie_for_valid_credentials(self, test_client, flask_app, create_user_via_api):
        """Login sets JWT cookie when credentials are valid"""
        # Create test user via API (but use a gated email for signup)
        create_user_via_api(
            {
                "first_name": "Neeraj",
                "last_name": "Samtani",
                "email": "neerajjsamtani@gmail.com",  # Gated user
                "password": "testpassword123",
            }
        )

        # Test API call with correct credentials
        login_data = {
            "email": "neerajjsamtani@gmail.com",
            "password": "testpassword123",
        }

        response = test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.get_json()
        assert data["login"] is True

        # Check that JWT cookies are set
        assert "access_token_cookie" in response.headers.get("Set-Cookie", "")

    def test_login_fails_for_nonexistent_email(self, test_client):
        """Login fails when email does not exist"""
        # Test API call with non-existent email
        login_data = {
            "email": "nonexistent@example.com",
            "password": "testpassword123",
        }

        response = test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "Email or password invalid"

    def test_login_fails_for_wrong_password(self, test_client, flask_app, create_user_via_api):
        """Login fails when password is incorrect"""
        # Create test user via API
        create_user_via_api(
            {
                "first_name": "Neeraj",
                "last_name": "Samtani",
                "email": "neerajjsamtani@gmail.com",  # Gated user
                "password": "correctpassword",
            }
        )

        # Test API call with wrong password
        login_data = {
            "email": "neerajjsamtani@gmail.com",
            "password": "wrongpassword",
        }

        response = test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "Email or password invalid"

    def test_login_requires_email_and_password(self, test_client):
        """Login fails when required fields are missing"""
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

    def test_logout_clears_jwt_cookie(self, test_client):
        """Logout clears the JWT cookie"""
        response = test_client.post("/api/auth/logout")

        assert response.status_code == 200
        data = response.get_json()
        assert data["logout"] is True

        # Check that JWT cookies are unset
        set_cookie_header = response.headers.get("Set-Cookie", "")
        assert "access_token_cookie=;" in set_cookie_header or "access_token_cookie=; " in set_cookie_header

    def test_current_user_returns_user_data_when_authenticated(self, test_client, flask_app, create_user_via_api):
        """Current user endpoint returns user data when authenticated"""
        # Create and log in a user
        create_user_via_api(
            {
                "first_name": "Neeraj",
                "last_name": "Samtani",
                "email": "neerajjsamtani@gmail.com",
                "password": "testpassword123",
            }
        )

        # Log in to get JWT cookie
        login_response = test_client.post(
            "/api/auth/login",
            json={
                "email": "neerajjsamtani@gmail.com",
                "password": "testpassword123",
            },
        )
        assert login_response.status_code == 200

        # Call /api/auth/me - cookies are automatically sent by test_client
        response = test_client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.get_json()
        assert data["email"] == "neerajjsamtani@gmail.com"
        assert data["first_name"] == "Neeraj"
        assert data["last_name"] == "Samtani"
        assert "id" in data

    def test_current_user_returns_401_without_jwt(self, test_client):
        """Current user endpoint returns 401 when not authenticated"""
        response = test_client.get("/api/auth/me")

        assert response.status_code == 401

    def test_current_user_returns_401_after_logout(self, test_client, create_user_via_api):
        """Current user endpoint returns 401 after user logs out"""
        # Create and log in a user
        create_user_via_api(
            {
                "first_name": "Neeraj",
                "last_name": "Samtani",
                "email": "neerajjsamtani@gmail.com",
                "password": "testpassword123",
            }
        )

        test_client.post(
            "/api/auth/login",
            json={
                "email": "neerajjsamtani@gmail.com",
                "password": "testpassword123",
            },
        )

        # Verify authenticated
        response = test_client.get("/api/auth/me")
        assert response.status_code == 200

        # Log out
        test_client.post("/api/auth/logout")

        # Should now be unauthenticated
        response = test_client.get("/api/auth/me")
        assert response.status_code == 401


class TestAuthFunctions:
    def test_user_can_be_found_by_email(self, flask_app, pg_session):
        """User can be retrieved by their email address"""
        from tests.test_helpers import setup_test_user

        with flask_app.app_context():
            from dao import get_user_by_email

            test_user = {
                "id": "test_user",
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "password_hash": "test_hash",
            }
            setup_test_user(pg_session, test_user)
            pg_session.commit()

            # Test function call
            found_user = get_user_by_email("test@example.com")

            assert found_user is not None
            assert found_user["email"] == "test@example.com"
            assert found_user["first_name"] == "Test"
            assert found_user["last_name"] == "User"

    def test_nonexistent_email_returns_none(self, flask_app):
        """Looking up a nonexistent email returns None"""
        with flask_app.app_context():
            from dao import get_user_by_email

            # Test function call with non-existent email
            found_user = get_user_by_email("nonexistent@example.com")

            assert found_user is None

    def test_gated_users_list_includes_allowed_emails(self):
        """Gated users list contains emails allowed for private beta"""
        assert isinstance(GATED_USERS, list)
        assert len(GATED_USERS) > 0
        assert "neerajjsamtani@gmail.com" in GATED_USERS

    def test_hashed_password_can_be_verified(self, flask_app):
        """Hashed password can be verified with original password"""
        with flask_app.app_context():
            from helpers import check_password, hash_password

            password = "testpassword123"
            hashed = hash_password(password)

            # Should be able to check the password
            assert check_password(hashed, password) is True
            assert check_password(hashed, "wrongpassword") is False

    def test_jwt_token_contains_user_identity(self, flask_app):
        """JWT token encodes and preserves user identity"""
        with flask_app.app_context():
            from flask_jwt_extended import create_access_token, decode_token

            # Create a token
            user_id = "test_user_id"
            token = create_access_token(identity=user_id)

            # Decode the token
            decoded = decode_token(token)
            assert decoded["sub"] == user_id
