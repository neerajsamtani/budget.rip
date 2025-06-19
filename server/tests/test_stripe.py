from unittest.mock import MagicMock, Mock, patch

import pytest
import stripe

from dao import (
    bank_accounts_collection,
    line_items_collection,
    stripe_raw_transaction_data_collection,
    upsert_with_id,
)
from resources.stripe import refresh_stripe, stripe_to_line_items


@pytest.fixture
def mock_stripe_customer():
    """Mock Stripe customer object"""
    customer = Mock()
    customer.id = "cus_test123"
    customer.email = "test@example.com"
    customer.name = "Test User"
    return customer


@pytest.fixture
def mock_stripe_session():
    """Mock Stripe financial connections session"""
    session = Mock()
    session.id = "fcsess_test123"
    session.accounts = [
        {
            "id": "fca_test123",
            "institution_name": "Test Bank",
            "display_name": "Checking Account",
            "last4": "1234",
            "status": "active",
        }
    ]
    return session


@pytest.fixture
def mock_stripe_account():
    """Mock Stripe financial connections account"""
    account = Mock()
    account.id = "fca_test123"
    account.institution_name = "Test Bank"
    account.display_name = "Checking Account"
    account.last4 = "1234"
    account.status = "active"
    account.authorization = "fcauth_test123"
    return account


@pytest.fixture
def mock_stripe_transaction():
    """Mock Stripe transaction data"""
    return {
        "id": "fct_test123",
        "account": "fca_test123",
        "amount": -5000,  # $50.00 in cents
        "description": "Test transaction",
        "status": "posted",
        "transacted_at": 1673778600,
    }


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


class TestStripeAPI:
    @patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
    @patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")
    def test_refresh_stripe_api_success(self, test_client, jwt_token, flask_app):
        """Test GET /api/refresh/stripe endpoint - success case"""
        with patch("resources.stripe.refresh_stripe") as mock_refresh:
            response = test_client.get(
                "/api/refresh/stripe",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            assert (
                response.get_data(as_text=True).strip()
                == '"Refreshed Stripe Connection"'
            )
            mock_refresh.assert_called_once()

    def test_refresh_stripe_api_unauthorized(self, test_client):
        """Test GET /api/refresh/stripe endpoint - unauthorized"""
        response = test_client.get("/api/refresh/stripe")
        assert response.status_code == 401

    @patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
    @patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")
    def test_create_fc_session_api_success(self, test_client, jwt_token, flask_app):
        """Test POST /api/create-fc-session endpoint - success case"""
        with flask_app.app_context():
            with patch(
                "resources.stripe.stripe.Customer.retrieve"
            ) as mock_retrieve, patch("resources.stripe.requests.post") as mock_post:
                # Mock customer retrieval
                mock_customer = MagicMock()
                mock_customer.id = "cus_test123"
                mock_customer.__getitem__.side_effect = lambda k: getattr(
                    mock_customer, k
                )
                mock_retrieve.return_value = mock_customer

                # Mock successful response
                mock_response = Mock()
                mock_response.json.return_value = {
                    "client_secret": "fcsess_test123_secret"
                }
                mock_post.return_value = mock_response

                response = test_client.post(
                    "/api/create-fc-session",
                    headers={"Authorization": "Bearer " + jwt_token},
                )

                assert response.status_code == 200
                data = response.get_json()
                assert "clientSecret" in data
                assert data["clientSecret"] == "fcsess_test123_secret"

    @patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
    @patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")
    def test_create_fc_session_api_customer_not_found(
        self, test_client, jwt_token, flask_app
    ):
        """Test POST /api/create-fc-session endpoint - customer not found"""
        with flask_app.app_context():
            with patch(
                "resources.stripe.stripe.Customer.retrieve"
            ) as mock_retrieve, patch(
                "resources.stripe.stripe.Customer.create"
            ) as mock_create, patch(
                "resources.stripe.requests.post"
            ) as mock_post:
                # Mock customer not found, then creation
                mock_retrieve.side_effect = stripe.InvalidRequestError(
                    message="Customer not found", param=None
                )
                mock_customer = MagicMock()
                mock_customer.id = "cus_new123"
                mock_customer.__getitem__.side_effect = lambda k: getattr(
                    mock_customer, k
                )
                mock_create.return_value = mock_customer

                # Mock successful response
                mock_response = Mock()
                mock_response.json.return_value = {
                    "client_secret": "fcsess_test123_secret"
                }
                mock_post.return_value = mock_response

                response = test_client.post(
                    "/api/create-fc-session",
                    headers={"Authorization": "Bearer " + jwt_token},
                )

                assert response.status_code == 200
                mock_create.assert_called_once()

    def test_create_accounts_api_success(self, test_client, jwt_token, flask_app):
        """Test POST /api/create_accounts endpoint - success case"""
        with flask_app.app_context():
            test_accounts = [
                {
                    "id": "fca_test123",
                    "institution_name": "Test Bank",
                    "display_name": "Checking Account",
                    "last4": "1234",
                }
            ]

            response = test_client.post(
                "/api/create_accounts",
                headers={"Authorization": "Bearer " + jwt_token},
                json=test_accounts,
            )

            assert response.status_code == 201
            data = response.get_json()
            assert "data" in data
            assert len(data["data"]) == 1

    def test_create_accounts_api_empty_list(self, test_client, jwt_token):
        """Test POST /api/create_accounts endpoint - empty accounts list"""
        response = test_client.post(
            "/api/create_accounts",
            headers={"Authorization": "Bearer " + jwt_token},
            json=[],
        )

        assert response.status_code == 400
        assert "No Accounts Submitted" in response.get_data(as_text=True)

    @patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
    @patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")
    def test_get_accounts_api_success(self, test_client, jwt_token, flask_app):
        """Test GET /api/get_accounts/<session_id> endpoint - success case"""
        with flask_app.app_context():
            with patch(
                "resources.stripe.stripe.financial_connections.Session.retrieve"
            ) as mock_retrieve, patch(
                "resources.stripe.bulk_upsert"
            ) as mock_bulk_upsert:
                # Mock session with accounts
                mock_session = MagicMock()
                accounts_list = [
                    {
                        "id": "fca_test123",
                        "institution_name": "Test Bank",
                        "display_name": "Checking Account",
                        "last4": "1234",
                    }
                ]
                mock_session.__getitem__.side_effect = lambda k: (
                    accounts_list if k == "accounts" else None
                )
                mock_retrieve.return_value = mock_session

                response = test_client.get(
                    "/api/get_accounts/fcsess_test123",
                    headers={"Authorization": "Bearer " + jwt_token},
                )

                assert response.status_code == 200
                data = response.get_json()
                assert "accounts" in data
                assert len(data["accounts"]) == 1

    @patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
    @patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")
    def test_get_accounts_and_balances_api_success(
        self, test_client, jwt_token, flask_app
    ):
        """Test GET /api/accounts_and_balances endpoint - success case"""
        with flask_app.app_context():
            # Insert test account data
            test_account = {
                "id": "fca_test123",
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
                "status": "active",
            }
            upsert_with_id(bank_accounts_collection, test_account, test_account["id"])

            with patch("resources.stripe.requests.get") as mock_get:
                # Mock balance response
                mock_response = Mock()
                mock_response.json.return_value = {
                    "data": [
                        {
                            "current": {"usd": 10000},  # $100.00 in cents
                            "as_of": "2023-01-15T10:30:00Z",
                        }
                    ]
                }
                mock_get.return_value = mock_response

                response = test_client.get(
                    "/api/accounts_and_balances",
                    headers={"Authorization": "Bearer " + jwt_token},
                )

                assert response.status_code == 200
                data = response.get_json()
                assert "fca_test123" in data
                account_data = data["fca_test123"]
                assert account_data["balance"] == 100.0
                assert account_data["name"] == "Test Bank Checking Account 1234"

    @patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
    @patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")
    def test_subscribe_to_account_api_success(self, test_client, jwt_token, flask_app):
        """Test GET /api/subscribe_to_account/<account_id> endpoint - success case"""
        with flask_app.app_context():
            with patch("resources.stripe.requests.post") as mock_post:
                # Mock successful subscription response
                mock_response = Mock()
                mock_response.text = '{"transaction_refresh": {"status": "succeeded"}}'
                mock_post.return_value = mock_response

                response = test_client.get(
                    "/api/subscribe_to_account/fca_test123",
                    headers={"Authorization": "Bearer " + jwt_token},
                )

                assert response.status_code == 200
                assert response.get_data(as_text=True).strip() == '"succeeded"'

    @patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
    @patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")
    def test_refresh_account_api_success(self, test_client, flask_app):
        """Test GET /api/refresh_account/<account_id> endpoint - success case"""
        with flask_app.app_context():
            with patch(
                "resources.stripe.stripe.financial_connections.Account.retrieve"
            ) as mock_retrieve, patch("resources.stripe.upsert") as mock_upsert:
                # Mock account
                mock_account = MagicMock()
                mock_account.id = "fca_test123"
                mock_account.__getitem__.side_effect = lambda k: getattr(
                    mock_account, k
                )
                mock_retrieve.return_value = mock_account

                response = test_client.get("/api/refresh_account/fca_test123")

                assert response.status_code == 200
                data = response.get_json()
                assert data["data"] == "success"

    @patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
    @patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")
    def test_relink_account_api_success(self, test_client, jwt_token, flask_app):
        """Test GET /api/relink_account/<account_id> endpoint - success case"""
        with flask_app.app_context():
            with patch(
                "resources.stripe.stripe.financial_connections.Account.retrieve"
            ) as mock_retrieve, patch(
                "resources.stripe.requests.get"
            ) as mock_get, patch(
                "resources.stripe.create_fc_session_api"
            ) as mock_create_session:
                # Mock account
                mock_account = MagicMock()
                mock_account.id = "fca_test123"
                mock_account.authorization = "fcauth_test123"
                mock_account.__getitem__.side_effect = lambda k: getattr(
                    mock_account, k
                )
                mock_retrieve.return_value = mock_account

                # Mock authorization response indicating relink required
                mock_auth_response = Mock()
                mock_auth_response.json.return_value = {
                    "status_details": {"inactive": {"action": "relink_required"}}
                }
                mock_get.return_value = mock_auth_response

                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.json = {"client_secret": "fcsess_test123_secret"}
                mock_create_session.return_value = mock_session_response

                response = test_client.get(
                    "/api/relink_account/fca_test123",
                    headers={"Authorization": "Bearer " + jwt_token},
                )

                assert response.status_code == 200
                data = response.get_json()
                assert "client_secret" in data

    @patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
    @patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")
    def test_relink_account_api_not_required(self, test_client, jwt_token, flask_app):
        """Test GET /api/relink_account/<account_id> endpoint - relink not required"""
        with flask_app.app_context():
            with patch(
                "resources.stripe.stripe.financial_connections.Account.retrieve"
            ) as mock_retrieve, patch("resources.stripe.requests.get") as mock_get:
                # Mock account
                mock_account = MagicMock()
                mock_account.id = "fca_test123"
                mock_account.authorization = "fcauth_test123"
                mock_account.__getitem__.side_effect = lambda k: getattr(
                    mock_account, k
                )
                mock_retrieve.return_value = mock_account

                # Mock authorization response indicating relink not required
                mock_auth_response = Mock()
                mock_auth_response.json.return_value = {
                    "status_details": {"inactive": {"action": "other_action"}}
                }
                mock_get.return_value = mock_auth_response

                response = test_client.get(
                    "/api/relink_account/fca_test123",
                    headers={"Authorization": "Bearer " + jwt_token},
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data["relink_required"] == False

    @patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
    @patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")
    def test_refresh_transactions_api_success(self, test_client, flask_app):
        """Test GET /api/refresh_transactions/<account_id> endpoint - success case"""
        with flask_app.app_context():
            with patch("resources.stripe.requests.get") as mock_get, patch(
                "resources.stripe.bulk_upsert"
            ) as mock_bulk_upsert:
                # Mock transaction response
                mock_response = Mock()
                mock_response.json.return_value = {
                    "data": [
                        {
                            "id": "fct_test123",
                            "account": "fca_test123",
                            "amount": -5000,
                            "description": "Test transaction",
                            "status": "posted",
                            "transacted_at": 1673778600,
                        }
                    ],
                    "has_more": False,
                }
                mock_response.text = '{"data": [{"id": "fct_test123", "account": "fca_test123", "amount": -5000, "description": "Test transaction", "status": "posted", "transacted_at": 1673778600}], "has_more": false}'
                mock_get.return_value = mock_response

                response = test_client.get("/api/refresh_transactions/fca_test123")

                assert response.status_code == 200
                assert (
                    "Refreshed Stripe Connection for Given Account"
                    in response.get_data(as_text=True)
                )


class TestStripeFunctions:
    def test_refresh_stripe_success(self, flask_app):
        """Test refresh_stripe function - success case"""
        with flask_app.app_context():
            # Insert test account data
            test_account = {
                "id": "fca_test123",
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
            }
            upsert_with_id(bank_accounts_collection, test_account, test_account["id"])

            with patch(
                "resources.stripe.refresh_account_api"
            ) as mock_refresh_account, patch(
                "resources.stripe.refresh_transactions_api"
            ) as mock_refresh_transactions, patch(
                "resources.stripe.stripe_to_line_items"
            ) as mock_convert:
                # Call the function
                refresh_stripe()

                # Verify all functions were called
                mock_refresh_account.assert_called_once_with("fca_test123")
                mock_refresh_transactions.assert_called_once_with("fca_test123")
                mock_convert.assert_called_once()

    def test_refresh_stripe_no_accounts(self, flask_app):
        """Test refresh_stripe function - no accounts to refresh"""
        with flask_app.app_context():
            with patch(
                "resources.stripe.refresh_account_api"
            ) as mock_refresh_account, patch(
                "resources.stripe.refresh_transactions_api"
            ) as mock_refresh_transactions, patch(
                "resources.stripe.stripe_to_line_items"
            ) as mock_convert:
                # Call the function with no accounts
                refresh_stripe()

                # Verify no refresh calls were made
                mock_refresh_account.assert_not_called()
                mock_refresh_transactions.assert_not_called()
                mock_convert.assert_called_once()

    def test_stripe_to_line_items_success(self, flask_app, mock_stripe_transaction):
        """Test stripe_to_line_items function - success case"""
        with flask_app.app_context():
            # Insert test data
            test_account = {
                "id": "fca_test123",
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
            }
            upsert_with_id(bank_accounts_collection, test_account, test_account["id"])

            test_transaction = mock_stripe_transaction
            upsert_with_id(
                stripe_raw_transaction_data_collection,
                test_transaction,
                test_transaction["id"],
            )

            with patch("resources.stripe.bulk_upsert") as mock_bulk_upsert:
                # Call the function
                stripe_to_line_items()

                # Verify bulk_upsert was called with line items
                mock_bulk_upsert.assert_called_once()
                call_args = mock_bulk_upsert.call_args
                assert call_args[0][0] == line_items_collection

                # Check that line items were created correctly
                line_items = call_args[0][1]
                assert len(line_items) == 1

                line_item = line_items[0]
                assert line_item.id == "line_item_fct_test123"
                assert line_item.responsible_party == "Test transaction"
                assert line_item.payment_method == "Checking Account"
                assert line_item.description == "Test transaction"
                assert line_item.amount == 50.0  # flip_amount(-5000) / 100 = 50.0

    def test_stripe_to_line_items_no_transactions(self, flask_app):
        """Test stripe_to_line_items function - no transactions to process"""
        with flask_app.app_context():
            with patch("resources.stripe.bulk_upsert") as mock_bulk_upsert:
                # Call the function with no transactions
                stripe_to_line_items()

                # Verify bulk_upsert was not called
                mock_bulk_upsert.assert_not_called()

    def test_stripe_to_line_items_account_not_found(
        self, flask_app, mock_stripe_transaction
    ):
        """Test stripe_to_line_items function - account not found"""
        with flask_app.app_context():
            # Insert transaction without corresponding account
            test_transaction = mock_stripe_transaction
            upsert_with_id(
                stripe_raw_transaction_data_collection,
                test_transaction,
                test_transaction["id"],
            )

            with patch("resources.stripe.bulk_upsert") as mock_bulk_upsert:
                # Call the function
                stripe_to_line_items()

                # Verify bulk_upsert was called with fallback payment method
                mock_bulk_upsert.assert_called_once()
                call_args = mock_bulk_upsert.call_args
                line_items = call_args[0][1]
                assert len(line_items) == 1
                assert line_items[0].payment_method == "Stripe"  # Fallback

    def test_stripe_to_line_items_batch_processing(self, flask_app):
        """Test stripe_to_line_items function - batch processing"""
        with flask_app.app_context():
            # Insert test account
            test_account = {
                "id": "fca_test123",
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
            }
            upsert_with_id(bank_accounts_collection, test_account, test_account["id"])

            # Insert multiple transactions
            transactions = []
            for i in range(1500):  # More than batch size of 1000
                transaction = {
                    "id": f"fct_test{i}",
                    "account": "fca_test123",
                    "amount": -1000,  # $10.00 in cents
                    "description": f"Test transaction {i}",
                    "status": "posted",
                    "transacted_at": 1673778600 + i,
                }
                transactions.append(transaction)
                upsert_with_id(
                    stripe_raw_transaction_data_collection,
                    transaction,
                    transaction["id"],
                )

            with patch("resources.stripe.bulk_upsert") as mock_bulk_upsert:
                # Call the function
                stripe_to_line_items()

                # Verify bulk_upsert was called multiple times (batches)
                assert mock_bulk_upsert.call_count >= 2

                # Verify all line items were created
                all_line_items = []
                for call in mock_bulk_upsert.call_args_list:
                    all_line_items.extend(call[0][1])

                assert len(all_line_items) == 1500


class TestStripeIntegration:
    def test_full_refresh_workflow(self, flask_app):
        """Test the complete refresh workflow from API to database"""
        with flask_app.app_context():
            # Insert test account
            test_account = {
                "id": "fca_test123",
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
            }
            upsert_with_id(bank_accounts_collection, test_account, test_account["id"])

            # Insert test transaction
            test_transaction = {
                "id": "fct_test123",
                "account": "fca_test123",
                "amount": -2500,  # $25.00 in cents
                "description": "Integration test transaction",
                "status": "posted",
                "transacted_at": 1673778600,
            }
            upsert_with_id(
                stripe_raw_transaction_data_collection,
                test_transaction,
                test_transaction["id"],
            )

            with patch(
                "resources.stripe.refresh_account_api"
            ) as mock_refresh_account, patch(
                "resources.stripe.refresh_transactions_api"
            ) as mock_refresh_transactions, patch(
                "resources.stripe.bulk_upsert"
            ) as mock_bulk_upsert:
                # Call refresh function
                refresh_stripe()

                # Verify refresh functions were called
                mock_refresh_account.assert_called_once_with("fca_test123")
                mock_refresh_transactions.assert_called_once_with("fca_test123")

                # Verify line items were created
                mock_bulk_upsert.assert_called_once()
                call_args = mock_bulk_upsert.call_args
                assert call_args[0][0] == line_items_collection

                line_items = call_args[0][1]
                assert len(line_items) == 1
                assert line_items[0].description == "Integration test transaction"
                assert line_items[0].payment_method == "Checking Account"
                assert line_items[0].amount == 25.0
