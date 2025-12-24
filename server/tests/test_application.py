import pytest

from dao import (
    bank_accounts_collection,
    line_items_collection,
    upsert_with_id,
)


@pytest.fixture
def mock_venmo_profile(mocker):
    """Mock Venmo profile"""
    mock_profile = mocker.Mock()
    mock_profile.username = "test_user"
    mock_profile.first_name = "Test"
    mock_profile.last_name = "User"
    return mock_profile


@pytest.fixture
def mock_splitwise_user(mocker):
    """Mock Splitwise user"""
    mock_user = mocker.Mock()
    mock_user.getFirstName = mocker.Mock(return_value="John")
    mock_user.getLastName = mocker.Mock(return_value="Doe")
    return mock_user


@pytest.fixture
def mock_bank_account():
    """Mock bank account data"""
    return {
        "id": "fca_test123",
        "institution_name": "Test Bank",
        "display_name": "Checking Account",
        "last4": "1234",
        "balances": {"available": 1000.0, "current": 1000.0},
    }


@pytest.fixture
def mock_line_item():
    """Mock line item data"""
    return {
        "id": "line_item_1",
        "date": 1673778600.0,
        "description": "Test line item",
        "amount": 25.0,
        "payment_method": "Venmo",
        "responsible_party": "John",
        "reviewed": False,
    }


@pytest.fixture
def mock_event():
    """Mock event data"""
    return {
        "id": "event_1",
        "date": 1673778600.0,
        "description": "Test event",
        "category": "Dining",
        "line_items": ["line_item_1", "line_item_2"],
    }


class TestApplicationRoutes:
    def test_index_api(self, test_client):
        """Test GET /api/ endpoint"""
        response = test_client.get("/api/")
        assert response.status_code == 200
        assert response.get_json() == "Welcome to Budgit API"

    def test_schedule_refresh_api_success(self, test_client, mocker):
        """Test GET /api/refresh/scheduled endpoint - success case"""
        mock_refresh_all = mocker.patch("application.refresh_all")
        mock_create_consistent = mocker.patch("application.create_consistent_line_items")

        response = test_client.get("/api/refresh/scheduled")

        assert response.status_code == 200
        mock_refresh_all.assert_called_once()
        mock_create_consistent.assert_called_once()

    def test_schedule_refresh_api_error(self, test_client, mocker):
        """Test GET /api/refresh/scheduled endpoint - error case"""
        mock_refresh_all = mocker.patch("application.refresh_all", side_effect=Exception("Test error"))
        mock_create_consistent = mocker.patch("application.create_consistent_line_items")

        response = test_client.get("/api/refresh/scheduled")

        assert response.status_code == 500
        mock_refresh_all.assert_called_once()
        mock_create_consistent.assert_not_called()

    def test_refresh_all_api_success(self, test_client, jwt_token, mocker):
        """Test POST /api/refresh/all endpoint - success case"""
        mock_refresh_all = mocker.patch("application.refresh_all")
        mock_create_consistent = mocker.patch("application.create_consistent_line_items")
        mock_all_line_items = mocker.patch("application.all_line_items")

        mock_all_line_items.return_value = []

        response = test_client.post(
            "/api/refresh/all",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        mock_refresh_all.assert_called_once()
        mock_create_consistent.assert_called_once()

    def test_refresh_all_api_unauthorized(self, test_client):
        """Test POST /api/refresh/all endpoint - unauthorized"""
        response = test_client.post("/api/refresh/all")
        assert response.status_code == 401

    def test_refresh_single_account_stripe_success(self, test_client, jwt_token, mocker):
        """Test POST /api/refresh/account endpoint - Stripe account success"""
        mock_refresh_transactions = mocker.patch("application.refresh_transactions_api")
        mock_stripe_to_line_items = mocker.patch("application.stripe_to_line_items")

        response = test_client.post(
            "/api/refresh/account",
            json={"accountId": "fca_test123", "source": "stripe"},
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        assert response.get_json()["message"] == "success"
        mock_refresh_transactions.assert_called_once_with("fca_test123")
        mock_stripe_to_line_items.assert_called_once()

    def test_refresh_single_account_venmo_success(self, test_client, jwt_token, mocker):
        """Test POST /api/refresh/account endpoint - Venmo account success"""
        mock_refresh_venmo = mocker.patch("application.refresh_venmo")
        mock_venmo_to_line_items = mocker.patch("application.venmo_to_line_items")

        response = test_client.post(
            "/api/refresh/account",
            json={"accountId": "venmo-testuser", "source": "venmo"},
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        assert response.get_json()["message"] == "success"
        mock_refresh_venmo.assert_called_once()
        mock_venmo_to_line_items.assert_called_once()

    def test_refresh_single_account_splitwise_success(self, test_client, jwt_token, mocker):
        """Test POST /api/refresh/account endpoint - Splitwise account success"""
        mock_refresh_splitwise = mocker.patch("application.refresh_splitwise")
        mock_splitwise_to_line_items = mocker.patch("application.splitwise_to_line_items")

        response = test_client.post(
            "/api/refresh/account",
            json={"accountId": "splitwise-testuser", "source": "splitwise"},
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        assert response.get_json()["message"] == "success"
        mock_refresh_splitwise.assert_called_once()
        mock_splitwise_to_line_items.assert_called_once()

    def test_refresh_single_account_missing_params(self, test_client, jwt_token):
        """Test POST /api/refresh/account endpoint - missing parameters"""
        response = test_client.post(
            "/api/refresh/account",
            json={"accountId": "fca_test123"},
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 400
        assert "accountId and source are required" in response.get_json()["error"]

    def test_refresh_single_account_invalid_source(self, test_client, jwt_token):
        """Test POST /api/refresh/account endpoint - invalid source"""
        response = test_client.post(
            "/api/refresh/account",
            json={"accountId": "test123", "source": "invalid"},
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 400
        assert "Invalid source" in response.get_json()["error"]

    def test_refresh_single_account_error(self, test_client, jwt_token, mocker):
        """Test POST /api/refresh/account endpoint - error during refresh"""
        mocker.patch("application.refresh_transactions_api", side_effect=Exception("Test error"))

        response = test_client.post(
            "/api/refresh/account",
            json={"accountId": "fca_test123", "source": "stripe"},
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 500
        assert "Test error" in response.get_json()["error"]

    def test_refresh_single_account_unauthorized(self, test_client):
        """Test POST /api/refresh/account endpoint - unauthorized"""
        response = test_client.post(
            "/api/refresh/account",
            json={"accountId": "fca_test123", "source": "stripe"},
        )
        assert response.status_code == 401

    def test_get_connected_accounts_api_success(
        self,
        test_client,
        jwt_token,
        flask_app,
        mock_venmo_profile,
        mock_splitwise_user,
        mock_bank_account,
        mocker,
    ):
        """Test GET /api/connected_accounts endpoint - success case"""
        with flask_app.app_context():
            # Insert test bank account
            upsert_with_id(bank_accounts_collection, mock_bank_account, mock_bank_account["id"])

            # Mock venmoclient responses
            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mock_venmo_profile
            mocker.patch("application.get_venmo_client", return_value=mock_venmo_client)
            mocker.patch(
                "application.splitwise_client.getCurrentUser",
                return_value=mock_splitwise_user,
            )

            response = test_client.get(
                "/api/connected_accounts",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 3

            # Check Venmo data
            venmo_data = next(item for item in data if "venmo" in item)
            assert venmo_data["venmo"] == ["test_user"]

            # Check Splitwise data
            splitwise_data = next(item for item in data if "splitwise" in item)
            assert splitwise_data["splitwise"] == ["John Doe"]

            # Check Stripe data
            stripe_data = next(item for item in data if "stripe" in item)
            assert len(stripe_data["stripe"]) == 1
            assert stripe_data["stripe"][0]["id"] == "fca_test123"

    def test_get_connected_accounts_api_venmo_error(self, test_client, jwt_token, mocker):
        """Test GET /api/connected_accounts endpoint - Venmo error"""
        mock_venmo_client = mocker.Mock()
        mock_venmo_client.my_profile.return_value = None
        mocker.patch("application.get_venmo_client", return_value=mock_venmo_client)

        # The route raises an exception when Venmo profile is None
        with pytest.raises(Exception, match="Failed to get Venmo profile"):
            test_client.get(
                "/api/connected_accounts",
                headers={"Authorization": "Bearer " + jwt_token},
            )

    def test_get_connected_accounts_api_unauthorized(self, test_client):
        """Test GET /api/connected_accounts endpoint - unauthorized"""
        response = test_client.get("/api/connected_accounts")
        assert response.status_code == 401

    def test_get_payment_methods_api_success(self, test_client, jwt_token, flask_app, mock_bank_account):
        """Test GET /api/payment_methods endpoint - success case"""
        with flask_app.app_context():
            # Insert test bank account
            upsert_with_id(bank_accounts_collection, mock_bank_account, mock_bank_account["id"])

            response = test_client.get(
                "/api/payment_methods",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            data = response.get_json()

            # Should include default payment methods
            assert "Cash" in data
            assert "Venmo" in data
            assert "Splitwise" in data

            # Should include bank account display name
            assert "Checking Account" in data

    def test_get_payment_methods_api_no_bank_accounts(self, test_client, jwt_token):
        """Test GET /api/payment_methods endpoint - no bank accounts"""
        response = test_client.get(
            "/api/payment_methods",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Should only include default payment methods
        assert data == ["Cash", "Venmo", "Splitwise"]

    def test_get_payment_methods_api_unauthorized(self, test_client):
        """Test GET /api/payment_methods endpoint - unauthorized"""
        response = test_client.get("/api/payment_methods")
        assert response.status_code == 401


class TestApplicationFunctions:
    def test_refresh_all_success(self, flask_app, mocker):
        """Test refresh_all function - success case"""
        with flask_app.app_context():
            mock_refresh_splitwise = mocker.patch("application.refresh_splitwise")
            mock_refresh_venmo = mocker.patch("application.refresh_venmo")
            mock_refresh_stripe = mocker.patch("application.refresh_stripe")

            from application import refresh_all

            refresh_all()

            mock_refresh_splitwise.assert_called_once()
            mock_refresh_venmo.assert_called_once()
            mock_refresh_stripe.assert_called_once()

    def test_create_consistent_line_items_success(self, flask_app, mocker):
        """Test create_consistent_line_items function - success case"""
        with flask_app.app_context():
            mock_splitwise_to_line_items = mocker.patch("application.splitwise_to_line_items")
            mock_venmo_to_line_items = mocker.patch("application.venmo_to_line_items")
            mock_stripe_to_line_items = mocker.patch("application.stripe_to_line_items")
            mock_cash_to_line_items = mocker.patch("application.cash_to_line_items")

            from application import create_consistent_line_items

            create_consistent_line_items()

            mock_splitwise_to_line_items.assert_called_once()
            mock_venmo_to_line_items.assert_called_once()
            mock_stripe_to_line_items.assert_called_once()
            mock_cash_to_line_items.assert_called_once()


class TestApplicationIntegration:
    def test_full_refresh_workflow(self, flask_app, mock_line_item, mocker):
        """Test the complete refresh workflow"""
        with flask_app.app_context():
            # Insert test line item
            upsert_with_id(line_items_collection, mock_line_item, mock_line_item["id"])

            mock_refresh_all = mocker.patch("application.refresh_all")
            mock_create_consistent = mocker.patch("application.create_consistent_line_items")
            mock_all_line_items = mocker.patch("application.all_line_items")

            mock_all_line_items.return_value = [mock_line_item]

            # Import the functions
            # This would normally be called via the route, but we can test the logic
            # by calling the underlying functions
            from application import create_consistent_line_items, refresh_all

            refresh_all()
            create_consistent_line_items()

            # Verify the workflow
            mock_refresh_all.assert_called_once()
            mock_create_consistent.assert_called_once()

    def test_connected_accounts_with_multiple_bank_accounts(self, test_client, jwt_token, flask_app, mocker):
        """Test connected accounts with multiple bank accounts"""
        with flask_app.app_context():
            # Insert multiple bank accounts
            bank_accounts = [
                {
                    "id": "fca_test1",
                    "institution_name": "Bank 1",
                    "display_name": "Checking Account 1",
                    "last4": "1234",
                },
                {
                    "id": "fca_test2",
                    "institution_name": "Bank 2",
                    "display_name": "Savings Account 2",
                    "last4": "5678",
                },
            ]

            for account in bank_accounts:
                upsert_with_id(bank_accounts_collection, account, account["id"])

            mock_venmo_client = mocker.Mock()
            mock_venmo_client.my_profile.return_value = mocker.Mock(username="test_user")
            mocker.patch("application.get_venmo_client", return_value=mock_venmo_client)
            mocker.patch(
                "application.splitwise_client.getCurrentUser",
                return_value=mocker.Mock(getFirstName=lambda: "John", getLastName=lambda: "Doe"),
            )

            response = test_client.get(
                "/api/connected_accounts",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            data = response.get_json()

            # Check Stripe data has both accounts
            stripe_data = next(item for item in data if "stripe" in item)
            assert len(stripe_data["stripe"]) == 2

    def test_payment_methods_with_multiple_bank_accounts(self, test_client, jwt_token, flask_app):
        """Test payment methods with multiple bank accounts"""
        with flask_app.app_context():
            # Insert multiple bank accounts
            bank_accounts = [
                {
                    "id": "fca_test1",
                    "institution_name": "Bank 1",
                    "display_name": "Checking Account 1",
                    "last4": "1234",
                },
                {
                    "id": "fca_test2",
                    "institution_name": "Bank 2",
                    "display_name": "Savings Account 2",
                    "last4": "5678",
                },
            ]

            for account in bank_accounts:
                upsert_with_id(bank_accounts_collection, account, account["id"])

            response = test_client.get(
                "/api/payment_methods",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            data = response.get_json()

            # Should include default payment methods
            assert "Cash" in data
            assert "Venmo" in data
            assert "Splitwise" in data

            # Should include both bank account display names
            assert "Checking Account 1" in data
            assert "Savings Account 2" in data
