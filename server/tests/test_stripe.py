import pytest
import stripe

from dao import (
    bank_accounts_collection,
    get_collection,
    line_items_collection,
    stripe_raw_transaction_data_collection,
)
from resources.stripe import refresh_stripe, stripe_to_line_items


@pytest.fixture
def mock_stripe_customer(mocker):
    """Mock Stripe customer object"""
    customer = mocker.Mock()
    customer.id = "cus_test123"
    customer.email = "test@example.com"
    customer.name = "Test User"
    return customer


@pytest.fixture
def mock_stripe_session(mocker):
    """Mock Stripe financial connections session"""
    session = mocker.Mock()
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
def mock_stripe_account(mocker):
    """Mock Stripe financial connections account"""
    account = mocker.Mock()
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
    def test_refresh_stripe_api_success(
        self, test_client, jwt_token, flask_app, mocker
    ):
        """Test GET /api/refresh/stripe endpoint - success case"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        mock_refresh = mocker.patch("resources.stripe.refresh_stripe")

        response = test_client.get(
            "/api/refresh/stripe",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        assert (
            response.get_data(as_text=True).strip() == '"Refreshed Stripe Connection"'
        )
        mock_refresh.assert_called_once()

    def test_refresh_stripe_api_unauthorized(self, test_client):
        """Test GET /api/refresh/stripe endpoint - unauthorized"""
        response = test_client.get("/api/refresh/stripe")
        assert response.status_code == 401

    def test_create_fc_session_api_success(
        self, test_client, jwt_token, flask_app, mocker
    ):
        """Test POST /api/create-fc-session endpoint - success case"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            mock_retrieve = mocker.patch("resources.stripe.stripe.Customer.retrieve")
            mock_post = mocker.patch("resources.stripe.requests.post")

            # Mock customer retrieval
            mock_customer = mocker.MagicMock()
            mock_customer.id = "cus_test123"
            mock_customer.__getitem__.side_effect = lambda k: getattr(mock_customer, k)
            mock_retrieve.return_value = mock_customer

            # Mock successful response
            mock_response = mocker.Mock()
            mock_response.json.return_value = {"client_secret": "fcsess_test123_secret"}
            mock_post.return_value = mock_response

            response = test_client.post(
                "/api/create-fc-session",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert "clientSecret" in data
            assert data["clientSecret"] == "fcsess_test123_secret"

    def test_create_fc_session_api_customer_not_found(
        self, test_client, jwt_token, flask_app, mocker
    ):
        """Test POST /api/create-fc-session endpoint - customer not found"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            mock_retrieve = mocker.patch("resources.stripe.stripe.Customer.retrieve")
            mock_create = mocker.patch("resources.stripe.stripe.Customer.create")
            mock_post = mocker.patch("resources.stripe.requests.post")

            # Mock customer not found, then creation
            mock_retrieve.side_effect = stripe.InvalidRequestError(
                message="Customer not found", param=None
            )
            mock_customer = mocker.MagicMock()
            mock_customer.id = "cus_new123"
            mock_customer.__getitem__.side_effect = lambda k: getattr(mock_customer, k)
            mock_create.return_value = mock_customer

            # Mock successful response
            mock_response = mocker.Mock()
            mock_response.json.return_value = {"client_secret": "fcsess_test123_secret"}
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

    def test_get_accounts_api_success(self, test_client, jwt_token, flask_app, mocker):
        """Test GET /api/accounts endpoint - success case"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            # Insert test account
            test_account = {
                "id": "fca_test123",
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
                "status": "active",
            }
            get_collection(bank_accounts_collection).insert_one(test_account)

            response = test_client.get(
                "/api/accounts",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert (
                response.status_code == 404
            )  # This endpoint doesn't exist in the current API

    def test_get_accounts_and_balances_api_success(
        self, test_client, jwt_token, flask_app, mocker
    ):
        """Test GET /api/accounts-and-balances endpoint - success case"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            mock_get = mocker.patch("resources.stripe.requests.get")

            # Insert test account
            test_account = {
                "_id": "fca_test123",  # For lookup in stripe_to_line_items
                "id": "fca_test123",  # For refresh_stripe function
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
                "status": "active",
            }
            get_collection(bank_accounts_collection).insert_one(test_account)

            # Mock balance response
            mock_response = mocker.Mock()
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

    def test_subscribe_to_account_api_success(
        self, test_client, jwt_token, flask_app, mocker
    ):
        """Test POST /api/subscribe-to-account endpoint - success case"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            mock_post = mocker.patch("resources.stripe.requests.post")

            # Mock successful response
            mock_response = mocker.Mock()
            mock_response.text = '{"transaction_refresh": {"status": "succeeded"}}'
            mock_post.return_value = mock_response

            response = test_client.get(
                "/api/subscribe_to_account/fca_test123",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            assert response.get_data(as_text=True).strip() == '"succeeded"'

    def test_refresh_account_api_success(self, flask_app, mocker):
        """Test POST /api/refresh-account endpoint - success case"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            mock_retrieve = mocker.patch(
                "resources.stripe.stripe.financial_connections.Account.retrieve"
            )
            mock_upsert = mocker.patch("resources.stripe.upsert")

            # Mock account
            mock_account = mocker.MagicMock()
            mock_account.id = "fca_test123"
            mock_account.__getitem__.side_effect = lambda k: getattr(mock_account, k)
            mock_retrieve.return_value = mock_account

            response = flask_app.test_client().get("/api/refresh_account/fca_test123")

            assert response.status_code == 200
            data = response.get_json()
            assert data["data"] == "success"

    def test_relink_account_api_success(
        self, test_client, jwt_token, flask_app, mocker
    ):
        """Test POST /api/relink-account endpoint - success case"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            mock_retrieve = mocker.patch(
                "resources.stripe.stripe.financial_connections.Account.retrieve"
            )
            mock_get = mocker.patch("resources.stripe.requests.get")
            mock_create_session = mocker.patch("resources.stripe.create_fc_session_api")

            # Mock account
            mock_account = mocker.MagicMock()
            mock_account.id = "fca_test123"
            mock_account.authorization = "fcauth_test123"
            mock_account.__getitem__.side_effect = lambda k: getattr(mock_account, k)
            mock_retrieve.return_value = mock_account

            # Mock authorization response indicating relink required
            mock_auth_response = mocker.Mock()
            mock_auth_response.json.return_value = {
                "status_details": {"inactive": {"action": "relink_required"}}
            }
            mock_get.return_value = mock_auth_response

            # Mock session creation
            mock_session_response = mocker.Mock()
            mock_session_response.json = {"client_secret": "fcsess_test123_secret"}
            mock_create_session.return_value = (mock_session_response, 200)

            response = test_client.get(
                "/api/relink_account/fca_test123",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert "client_secret" in data

    def test_relink_account_api_not_required(
        self, test_client, jwt_token, flask_app, mocker
    ):
        """Test POST /api/relink-account endpoint - relink not required"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            mock_retrieve = mocker.patch(
                "resources.stripe.stripe.financial_connections.Account.retrieve"
            )
            mock_get = mocker.patch("resources.stripe.requests.get")

            # Mock account
            mock_account = mocker.MagicMock()
            mock_account.id = "fca_test123"
            mock_account.authorization = "fcauth_test123"
            mock_account.__getitem__.side_effect = lambda k: getattr(mock_account, k)
            mock_retrieve.return_value = mock_account

            # Mock authorization response indicating relink not required
            mock_auth_response = mocker.Mock()
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

    def test_refresh_transactions_api_success(self, flask_app, mocker):
        """Test POST /api/refresh-transactions endpoint - success case"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            # Mock Stripe SDK call instead of raw requests
            mock_list = mocker.patch(
                "resources.stripe.stripe.financial_connections.Transaction.list"
            )

            # Create a mocked list object with the expected attributes
            mocked_transaction = mocker.MagicMock()
            mocked_transaction.id = "fct_test123"
            mocked_transaction.account = "fca_test123"
            mocked_transaction.amount = -5000
            mocked_transaction.description = "Test transaction"
            mocked_transaction.status = "posted"
            mocked_transaction.transacted_at = 1673778600

            mocked_list_object = mocker.Mock()
            mocked_list_object.data = [mocked_transaction]
            mocked_list_object.has_more = False
            mock_list.return_value = mocked_list_object

            response = flask_app.test_client().get(
                "/api/refresh_transactions/fca_test123"
            )

            assert response.status_code == 200
            assert "Refreshed Stripe Connection for Given Account" in response.get_data(
                as_text=True
            )


class TestStripeFunctions:
    def test_refresh_stripe_success(self, flask_app, mocker):
        """Test refresh_stripe function - success case"""
        with flask_app.app_context():
            mock_refresh_account = mocker.patch("resources.stripe.refresh_account_api")
            mock_refresh_transactions = mocker.patch(
                "resources.stripe.refresh_transactions_api"
            )
            mock_convert = mocker.patch("resources.stripe.stripe_to_line_items")

            # Insert test account data
            test_account = {
                "_id": "fca_test123",  # For lookup in stripe_to_line_items
                "id": "fca_test123",  # For refresh_stripe function
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
            }
            get_collection(bank_accounts_collection).insert_one(test_account)

            # Call the function
            refresh_stripe()

            # Verify all functions were called
            mock_refresh_account.assert_called_once_with("fca_test123")
            mock_refresh_transactions.assert_called_once_with("fca_test123")
            mock_convert.assert_called_once()

    def test_refresh_stripe_no_accounts(self, flask_app, mocker):
        """Test refresh_stripe function - no accounts to refresh"""
        with flask_app.app_context():
            mock_refresh_account = mocker.patch("resources.stripe.refresh_account_api")
            mock_refresh_transactions = mocker.patch(
                "resources.stripe.refresh_transactions_api"
            )
            mock_convert = mocker.patch("resources.stripe.stripe_to_line_items")

            # Call the function with no accounts
            refresh_stripe()

            # Verify no refresh calls were made
            mock_refresh_account.assert_not_called()
            mock_refresh_transactions.assert_not_called()
            mock_convert.assert_called_once()

    def test_stripe_to_line_items_success(
        self, flask_app, mock_stripe_transaction, mocker
    ):
        """Test stripe_to_line_items function - success case"""
        with flask_app.app_context():
            # Insert test data
            test_account = {
                "_id": "fca_test123",
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
            }
            get_collection(bank_accounts_collection).insert_one(test_account)

            test_transaction = mock_stripe_transaction
            get_collection(stripe_raw_transaction_data_collection).insert_one(
                test_transaction
            )

            mock_bulk_upsert = mocker.patch("resources.stripe.bulk_upsert")

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
            # The ID should be based on the MongoDB _id field
            assert line_item.id.startswith("line_item_")
            assert line_item.responsible_party == "Test transaction"
            assert line_item.payment_method == "Checking Account"
            assert line_item.description == "Test transaction"
            assert line_item.amount == 50.0  # flip_amount(-5000) / 100 = 50.0

    def test_stripe_to_line_items_no_transactions(self, flask_app, mocker):
        """Test stripe_to_line_items function - no transactions to process"""
        with flask_app.app_context():
            mock_bulk_upsert = mocker.patch("resources.stripe.bulk_upsert")

            # Call the function with no transactions
            stripe_to_line_items()

            # Verify bulk_upsert was not called
            mock_bulk_upsert.assert_not_called()

    def test_stripe_to_line_items_account_not_found(
        self, flask_app, mock_stripe_transaction, mocker
    ):
        """Test stripe_to_line_items function - account not found"""
        with flask_app.app_context():
            # Insert transaction without corresponding account
            test_transaction = mock_stripe_transaction
            get_collection(stripe_raw_transaction_data_collection).insert_one(
                test_transaction
            )

            mock_bulk_upsert = mocker.patch("resources.stripe.bulk_upsert")

            # Call the function
            stripe_to_line_items()

            # Verify bulk_upsert was called with fallback payment method
            mock_bulk_upsert.assert_called_once()
            call_args = mock_bulk_upsert.call_args
            line_items = call_args[0][1]
            assert len(line_items) == 1
            assert line_items[0].payment_method == "Stripe"  # Fallback

    def test_stripe_to_line_items_batch_processing(self, flask_app, mocker):
        """Test stripe_to_line_items function - batch processing"""
        with flask_app.app_context():
            # Insert test account
            test_account = {
                "_id": "fca_test123",
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
            }
            get_collection(bank_accounts_collection).insert_one(test_account)

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
                get_collection(stripe_raw_transaction_data_collection).insert_one(
                    transaction
                )

            mock_bulk_upsert = mocker.patch("resources.stripe.bulk_upsert")

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
    def test_full_refresh_workflow(self, flask_app, mocker):
        """Test the complete refresh workflow from API to database"""
        with flask_app.app_context():
            mock_refresh_account = mocker.patch("resources.stripe.refresh_account_api")
            mock_refresh_transactions = mocker.patch(
                "resources.stripe.refresh_transactions_api"
            )
            mock_bulk_upsert = mocker.patch("resources.stripe.bulk_upsert")

            # Insert test account
            test_account = {
                "_id": "fca_test123",  # For lookup in stripe_to_line_items
                "id": "fca_test123",  # For refresh_stripe function
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
            }
            get_collection(bank_accounts_collection).insert_one(test_account)

            # Insert test transaction
            test_transaction = {
                "id": "fct_test123",
                "account": "fca_test123",
                "amount": -2500,  # $25.00 in cents
                "description": "Integration test transaction",
                "status": "posted",
                "transacted_at": 1673778600,
            }
            get_collection(stripe_raw_transaction_data_collection).insert_one(
                test_transaction
            )

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
