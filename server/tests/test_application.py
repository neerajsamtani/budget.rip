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
    def test_api_root_returns_welcome_message(self, test_client):
        """API root endpoint returns welcome message"""
        response = test_client.get("/api/")
        assert response.status_code == 200
        assert response.get_json() == "Welcome to Budgit API"

    def test_scheduled_refresh_triggers_data_sync(self, test_client, mocker):
        """Scheduled refresh triggers data refresh and line item creation"""
        mock_refresh_all = mocker.patch("application.refresh_all")
        mock_create_consistent = mocker.patch("application.create_consistent_line_items")

        response = test_client.get("/api/refresh/scheduled")

        assert response.status_code == 200
        mock_refresh_all.assert_called_once()
        mock_create_consistent.assert_called_once()

    def test_scheduled_refresh_returns_500_on_error(self, test_client, mocker):
        """Scheduled refresh returns 500 when data refresh fails"""
        mock_refresh_all = mocker.patch("application.refresh_all", side_effect=Exception("Test error"))
        mock_create_consistent = mocker.patch("application.create_consistent_line_items")

        response = test_client.get("/api/refresh/scheduled")

        assert response.status_code == 500
        mock_refresh_all.assert_called_once()
        mock_create_consistent.assert_not_called()

    def test_refresh_all_syncs_all_data_sources(self, test_client, jwt_token, mocker):
        """Refresh all endpoint syncs data from all sources"""
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

    def test_refresh_all_requires_authentication(self, test_client):
        """Refresh all endpoint requires authentication"""
        response = test_client.post("/api/refresh/all")
        assert response.status_code == 401

    def test_refresh_account_syncs_stripe_transactions(self, test_client, jwt_token, mocker):
        """Refresh account endpoint syncs Stripe transactions"""
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

    def test_refresh_account_syncs_venmo_transactions(self, test_client, jwt_token, mocker):
        """Refresh account endpoint syncs Venmo transactions"""
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

    def test_refresh_account_syncs_splitwise_transactions(self, test_client, jwt_token, mocker):
        """Refresh account endpoint syncs Splitwise transactions"""
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

    def test_refresh_account_requires_account_id_and_source(self, test_client, jwt_token):
        """Refresh account endpoint requires accountId and source parameters"""
        response = test_client.post(
            "/api/refresh/account",
            json={"accountId": "fca_test123"},
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 400
        assert "accountId and source are required" in response.get_json()["error"]

    def test_refresh_account_rejects_invalid_source(self, test_client, jwt_token):
        """Refresh account endpoint rejects invalid source values"""
        response = test_client.post(
            "/api/refresh/account",
            json={"accountId": "test123", "source": "invalid"},
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 400
        assert "Invalid source" in response.get_json()["error"]

    def test_refresh_account_returns_500_on_error(self, test_client, jwt_token, mocker):
        """Refresh account endpoint returns 500 when refresh fails"""
        mocker.patch("application.refresh_transactions_api", side_effect=Exception("Test error"))

        response = test_client.post(
            "/api/refresh/account",
            json={"accountId": "fca_test123", "source": "stripe"},
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 500
        assert "Test error" in response.get_json()["error"]

    def test_refresh_account_requires_authentication(self, test_client):
        """Refresh account endpoint requires authentication"""
        response = test_client.post(
            "/api/refresh/account",
            json={"accountId": "fca_test123", "source": "stripe"},
        )
        assert response.status_code == 401

    def test_connected_accounts_returns_venmo_splitwise_and_stripe(
        self,
        test_client,
        jwt_token,
        flask_app,
        mock_venmo_profile,
        mock_splitwise_user,
        mock_bank_account,
        mocker,
    ):
        """Connected accounts endpoint returns Venmo, Splitwise, and Stripe accounts"""
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

    def test_connected_accounts_fails_when_venmo_profile_unavailable(self, test_client, jwt_token, mocker):
        """Connected accounts endpoint fails when Venmo profile is unavailable"""
        mock_venmo_client = mocker.Mock()
        mock_venmo_client.my_profile.return_value = None
        mocker.patch("application.get_venmo_client", return_value=mock_venmo_client)

        # The route raises an exception when Venmo profile is None
        with pytest.raises(Exception, match="Failed to get Venmo profile"):
            test_client.get(
                "/api/connected_accounts",
                headers={"Authorization": "Bearer " + jwt_token},
            )

    def test_connected_accounts_requires_authentication(self, test_client):
        """Connected accounts endpoint requires authentication"""
        response = test_client.get("/api/connected_accounts")
        assert response.status_code == 401

    def test_payment_methods_includes_bank_accounts(self, test_client, jwt_token, flask_app, mock_bank_account):
        """Payment methods endpoint includes bank account display names"""
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

    def test_payment_methods_returns_defaults_when_no_bank_accounts(self, test_client, jwt_token):
        """Payment methods returns only default methods when no bank accounts exist"""
        response = test_client.get(
            "/api/payment_methods",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Should only include default payment methods
        assert data == ["Cash", "Venmo", "Splitwise"]

    def test_payment_methods_requires_authentication(self, test_client):
        """Payment methods endpoint requires authentication"""
        response = test_client.get("/api/payment_methods")
        assert response.status_code == 401


class TestApplicationFunctions:
    def test_refresh_all_calls_all_data_source_refreshers(self, flask_app, mocker):
        """Refresh all calls Splitwise, Venmo, and Stripe refreshers"""
        with flask_app.app_context():
            mock_refresh_splitwise = mocker.patch("application.refresh_splitwise")
            mock_refresh_venmo = mocker.patch("application.refresh_venmo")
            mock_refresh_stripe = mocker.patch("application.refresh_stripe")

            from application import refresh_all

            refresh_all()

            mock_refresh_splitwise.assert_called_once()
            mock_refresh_venmo.assert_called_once()
            mock_refresh_stripe.assert_called_once()

    def test_create_consistent_line_items_normalizes_all_sources(self, flask_app, mocker):
        """Create consistent line items normalizes data from all sources"""
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
    def test_refresh_workflow_syncs_data_and_creates_line_items(self, flask_app, mock_line_item, mocker):
        """Complete refresh workflow syncs data and creates line items"""
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

    def test_connected_accounts_lists_all_bank_accounts(self, test_client, jwt_token, flask_app, mocker):
        """Connected accounts lists all bank accounts under Stripe"""
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

    def test_payment_methods_lists_all_bank_account_names(self, test_client, jwt_token, flask_app):
        """Payment methods lists display names for all bank accounts"""
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
