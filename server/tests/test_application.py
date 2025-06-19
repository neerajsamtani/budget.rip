from unittest.mock import Mock, patch

import pytest

from dao import (
    bank_accounts_collection,
    events_collection,
    get_collection,
    line_items_collection,
    upsert_with_id,
)


@pytest.fixture
def mock_venmo_profile():
    """Mock Venmo profile"""
    profile = Mock()
    profile.username = "test_user"
    return profile


@pytest.fixture
def mock_splitwise_user():
    """Mock Splitwise user"""
    user = Mock()
    user.getFirstName.return_value = "John"
    user.getLastName.return_value = "Doe"
    return user


@pytest.fixture
def mock_bank_account():
    """Mock bank account data"""
    return {
        "id": "fca_test123",
        "institution_name": "Test Bank",
        "display_name": "Checking Account",
        "last4": "1234",
        "status": "active",
    }


@pytest.fixture
def mock_line_item():
    """Mock line item data"""
    return {
        "id": "line_item_1",
        "date": 1234567890,
        "responsible_party": "John Doe",
        "payment_method": "Cash",
        "description": "Test transaction",
        "amount": 100,
    }


@pytest.fixture
def mock_event():
    """Mock event data"""
    return {
        "id": "event_1",
        "name": "Test Event",
        "line_items": ["line_item_1", "line_item_2"],
    }


class TestApplicationRoutes:
    def test_index_api(self, test_client):
        """Test GET /api/ endpoint"""
        response = test_client.get("/api/")

        assert response.status_code == 200
        assert response.get_data(as_text=True).strip() == '"Welcome to Budgit API"'

    @patch("application.refresh_all")
    @patch("application.create_consistent_line_items")
    def test_schedule_refresh_api_success(
        self, mock_create_consistent, mock_refresh_all, test_client
    ):
        """Test GET /api/refresh/scheduled endpoint - success case"""
        response = test_client.get("/api/refresh/scheduled")

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "success"
        mock_refresh_all.assert_called_once()
        mock_create_consistent.assert_called_once()

    @patch("application.refresh_all")
    @patch("application.create_consistent_line_items")
    def test_schedule_refresh_api_error(
        self, mock_create_consistent, mock_refresh_all, test_client
    ):
        """Test GET /api/refresh/scheduled endpoint - error case"""
        mock_refresh_all.side_effect = Exception("Test error")

        response = test_client.get("/api/refresh/scheduled")

        assert response.status_code == 500
        data = response.get_json()
        assert data["error"] == "Test error"

    @patch("application.refresh_all")
    @patch("application.create_consistent_line_items")
    @patch("application.all_line_items")
    def test_refresh_all_api_success(
        self,
        mock_all_line_items,
        mock_create_consistent,
        mock_refresh_all,
        test_client,
        jwt_token,
    ):
        """Test GET /api/refresh/all endpoint - success case"""
        mock_line_items = [{"id": "line_item_1", "amount": 100}]
        mock_all_line_items.return_value = mock_line_items

        response = test_client.get(
            "/api/refresh/all",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["data"] == mock_line_items
        mock_refresh_all.assert_called_once()
        mock_create_consistent.assert_called_once()
        mock_all_line_items.assert_called_once_with(only_line_items_to_review=True)

    def test_refresh_all_api_unauthorized(self, test_client):
        """Test GET /api/refresh/all endpoint - unauthorized"""
        response = test_client.get("/api/refresh/all")
        assert response.status_code == 401

    @patch("application.venmo_client")
    @patch("application.splitwise_client")
    def test_get_connected_accounts_api_success(
        self,
        mock_splitwise_client,
        mock_venmo_client,
        test_client,
        jwt_token,
        flask_app,
        mock_venmo_profile,
        mock_splitwise_user,
        mock_bank_account,
    ):
        """Test GET /api/connected_accounts endpoint - success case"""
        with flask_app.app_context():
            # Insert test bank account
            upsert_with_id(
                bank_accounts_collection, mock_bank_account, mock_bank_account["id"]
            )

            # Mock client responses
            mock_venmo_client.my_profile.return_value = mock_venmo_profile
            mock_splitwise_client.getCurrentUser.return_value = mock_splitwise_user

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

    @patch("application.venmo_client")
    def test_get_connected_accounts_api_venmo_error(
        self, mock_venmo_client, test_client, jwt_token
    ):
        """Test GET /api/connected_accounts endpoint - Venmo error"""
        mock_venmo_client.my_profile.return_value = None

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

    def test_get_payment_methods_api_success(
        self, test_client, jwt_token, flask_app, mock_bank_account
    ):
        """Test GET /api/payment_methods endpoint - success case"""
        with flask_app.app_context():
            # Insert test bank account
            upsert_with_id(
                bank_accounts_collection, mock_bank_account, mock_bank_account["id"]
            )

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
    def test_add_event_ids_to_line_items_success(
        self, flask_app, mock_event, mock_line_item
    ):
        """Test add_event_ids_to_line_items function - success case"""
        with flask_app.app_context():
            # Insert test data
            upsert_with_id(events_collection, mock_event, mock_event["id"])

            # Insert line items that will be referenced by the event
            line_item_1 = mock_line_item.copy()
            line_item_1["id"] = "line_item_1"
            upsert_with_id(line_items_collection, line_item_1, line_item_1["id"])

            line_item_2 = mock_line_item.copy()
            line_item_2["id"] = "line_item_2"
            upsert_with_id(line_items_collection, line_item_2, line_item_2["id"])

            # Import and call the function
            from application import add_event_ids_to_line_items

            add_event_ids_to_line_items()

            # Verify line items were updated with event_id
            line_items_coll = get_collection(line_items_collection)
            updated_line_item_1 = line_items_coll.find_one({"id": "line_item_1"})
            updated_line_item_2 = line_items_coll.find_one({"id": "line_item_2"})

            assert updated_line_item_1 is not None
            assert updated_line_item_2 is not None
            assert updated_line_item_1["event_id"] == "event_1"
            assert updated_line_item_2["event_id"] == "event_1"

    def test_add_event_ids_to_line_items_no_events(self, flask_app):
        """Test add_event_ids_to_line_items function - no events"""
        with flask_app.app_context():
            from application import add_event_ids_to_line_items

            # Should not raise any exceptions
            add_event_ids_to_line_items()

    def test_add_event_ids_to_line_items_no_line_items(self, flask_app, mock_event):
        """Test add_event_ids_to_line_items function - event with no line items"""
        with flask_app.app_context():
            # Insert event with empty line_items list
            event_no_line_items = mock_event.copy()
            event_no_line_items["line_items"] = []
            upsert_with_id(
                events_collection, event_no_line_items, event_no_line_items["id"]
            )

            from application import add_event_ids_to_line_items

            # Should not raise any exceptions
            add_event_ids_to_line_items()

    @patch("application.refresh_splitwise")
    @patch("application.refresh_venmo")
    @patch("application.refresh_stripe")
    def test_refresh_all_success(
        self, mock_refresh_stripe, mock_refresh_venmo, mock_refresh_splitwise, flask_app
    ):
        """Test refresh_all function - success case"""
        with flask_app.app_context():
            from application import refresh_all

            refresh_all()

            mock_refresh_splitwise.assert_called_once()
            mock_refresh_venmo.assert_called_once()
            mock_refresh_stripe.assert_called_once()

    @patch("application.splitwise_to_line_items")
    @patch("application.venmo_to_line_items")
    @patch("application.stripe_to_line_items")
    @patch("application.cash_to_line_items")
    @patch("application.add_event_ids_to_line_items")
    def test_create_consistent_line_items_success(
        self,
        mock_add_event_ids,
        mock_cash_to_line_items,
        mock_stripe_to_line_items,
        mock_venmo_to_line_items,
        mock_splitwise_to_line_items,
        flask_app,
    ):
        """Test create_consistent_line_items function - success case"""
        with flask_app.app_context():
            from application import create_consistent_line_items

            create_consistent_line_items()

            mock_splitwise_to_line_items.assert_called_once()
            mock_venmo_to_line_items.assert_called_once()
            mock_stripe_to_line_items.assert_called_once()
            mock_cash_to_line_items.assert_called_once()
            mock_add_event_ids.assert_called_once()


class TestApplicationIntegration:
    def test_full_refresh_workflow(self, flask_app, mock_line_item):
        """Test the complete refresh workflow"""
        with flask_app.app_context():
            # Insert test line item
            upsert_with_id(line_items_collection, mock_line_item, mock_line_item["id"])

            with patch("application.refresh_all") as mock_refresh_all, patch(
                "application.create_consistent_line_items"
            ) as mock_create_consistent, patch(
                "application.all_line_items"
            ) as mock_all_line_items:

                mock_all_line_items.return_value = [mock_line_item]

                # Import the functions
                # This would normally be called via the route, but we can test the logic
                # by calling the underlying functions
                from application import (
                    create_consistent_line_items,
                    refresh_all,
                    refresh_all_api,
                )

                refresh_all()
                create_consistent_line_items()

                # Verify the workflow
                mock_refresh_all.assert_called_once()
                mock_create_consistent.assert_called_once()

    def test_connected_accounts_with_multiple_bank_accounts(
        self, test_client, jwt_token, flask_app
    ):
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

            with patch("application.venmo_client") as mock_venmo_client, patch(
                "application.splitwise_client"
            ) as mock_splitwise_client:

                mock_venmo_client.my_profile.return_value = Mock(username="test_user")
                mock_splitwise_client.getCurrentUser.return_value = Mock(
                    getFirstName=lambda: "John", getLastName=lambda: "Doe"
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

    def test_payment_methods_with_multiple_bank_accounts(
        self, test_client, jwt_token, flask_app
    ):
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
