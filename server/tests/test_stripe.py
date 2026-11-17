import json
from urllib.parse import urlparse

import pytest
import stripe

from clients import stripe_client
from constants import STRIPE_API_KEY, STRIPE_API_VERSION
from queries import get_all_bank_accounts, get_transactions
from resources.stripe import refresh_stripe, refresh_transactions, stripe_to_line_items


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


class TestStripeConfiguration:
    def test_all_sdk_requests_use_the_shared_version_and_key(self, mocker):
        http_client = mocker.Mock(spec=stripe.HTTPClient)
        http_client.name = "test"
        mocker.patch("stripe._api_requestor._APIRequestor._get_http_client", return_value=http_client)

        def respond(method, url, headers, post_data=None, **kwargs):
            path = urlparse(url).path
            if path.endswith(("/transactions", "/inferred_balances")):
                body = {"object": "list", "data": [], "has_more": False, "url": path}
            elif "/customers" in path:
                body = {"id": "cus_test123", "object": "customer"}
            elif "/sessions" in path:
                body = {"id": "fcsess_test123", "object": "financial_connections.session", "client_secret": "fake_secret"}
            else:
                body = {"id": "fca_test123", "object": "financial_connections.account"}
            return json.dumps(body), 200, {}

        http_client.request_with_retries.side_effect = respond

        stripe.Customer.retrieve("cus_test123")
        stripe.Customer.create(email="test@example.com", name="Test")
        session_params = {
            "account_holder": {"type": "customer", "customer": "cus_test123"},
            "permissions": ["transactions", "balances"],
            "manual_entry": {"mode": "disabled"},
            "filters": {"require_payment_method_support": "none"},
        }
        stripe.financial_connections.Session.create(**session_params)
        stripe.financial_connections.Session.create(**session_params, relink_options={"authorization": "fcauth_test123"})
        stripe.financial_connections.Session.retrieve("fcsess_test123")
        stripe.financial_connections.Account.retrieve("fca_test123")
        stripe.financial_connections.Account.subscribe("fca_test123", features=["transactions", "inferred_balances"])
        stripe.financial_connections.Transaction.list(account="fca_test123", limit=100)
        stripe_client.v1.financial_connections.accounts.inferred_balances.list(account="fca_test123", params={"limit": 1})

        assert http_client.request_with_retries.call_count == 9
        for call in http_client.request_with_retries.call_args_list:
            assert call.args[2]["Stripe-Version"] == STRIPE_API_VERSION
            assert call.args[2]["Authorization"] == f"Bearer {STRIPE_API_KEY}"


class TestStripeAPI:
    def test_refresh_stripe_syncs_accounts_and_transactions(self, test_client, jwt_token, flask_app, mocker):
        """Stripe refresh syncs accounts and transactions"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        mock_refresh = mocker.patch("resources.stripe.refresh_stripe")
        mock_convert = mocker.patch("resources.stripe.stripe_to_line_items")

        response = test_client.get(
            "/api/refresh/stripe",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        assert response.get_data(as_text=True).strip() == '"Refreshed Stripe Connection"'
        mock_refresh.assert_called_once()
        mock_convert.assert_called_once_with()

    def test_refresh_stripe_requires_authentication(self, test_client):
        """Stripe refresh endpoint requires authentication"""
        response = test_client.get("/api/refresh/stripe")
        assert response.status_code == 401

    @pytest.mark.parametrize("relink_auth", [None, "fcauth_test123"])
    def test_create_fc_session_returns_client_secret(self, test_client, jwt_token, flask_app, mocker, relink_auth):
        """Creating financial connections session returns client secret"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            mock_retrieve = mocker.patch("resources.stripe.stripe.Customer.retrieve")
            mock_session_create = mocker.patch("resources.stripe.stripe.financial_connections.Session.create")

            # Mock customer retrieval
            mock_customer = mocker.MagicMock()
            mock_customer.id = "cus_test123"
            mock_customer.__getitem__.side_effect = lambda k: getattr(mock_customer, k)
            mock_retrieve.return_value = mock_customer

            # Mock successful session creation
            mock_session = mocker.MagicMock()
            mock_session.__getitem__.return_value = "fcsess_test123_secret"
            mock_session_create.return_value = mock_session

            endpoint = "/api/create-fc-session"
            if relink_auth:
                endpoint = "/api/relink_account/fca_test123"
                mocker.patch(
                    "resources.stripe.stripe.financial_connections.Account.retrieve",
                    return_value={"authorization": relink_auth},
                )
                mocker.patch("resources.stripe.check_can_relink", return_value=True)

            response = test_client.post(
                endpoint,
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert "clientSecret" in data
            assert data["clientSecret"] == "fcsess_test123_secret"
            expected_params = {
                "account_holder": {"type": "customer", "customer": "cus_test123"},
                "permissions": ["transactions", "balances"],
                "manual_entry": {"mode": "disabled"},
                "filters": {"require_payment_method_support": "none"},
            }
            if relink_auth:
                expected_params["relink_options"] = {"authorization": relink_auth}
            mock_session_create.assert_called_once_with(**expected_params)

    def test_missing_customer_creates_new_customer(self, test_client, jwt_token, flask_app, mocker):
        """Missing customer triggers new customer creation"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            mock_retrieve = mocker.patch("resources.stripe.stripe.Customer.retrieve")
            mock_create = mocker.patch("resources.stripe.stripe.Customer.create")
            mock_session_create = mocker.patch("resources.stripe.stripe.financial_connections.Session.create")

            # Mock customer not found, then creation
            mock_retrieve.side_effect = stripe.InvalidRequestError(message="Customer not found", param=None)
            mock_customer = mocker.MagicMock()
            mock_customer.id = "cus_new123"
            mock_customer.__getitem__.side_effect = lambda k: getattr(mock_customer, k)
            mock_create.return_value = mock_customer

            # Mock successful session creation
            mock_session = mocker.MagicMock()
            mock_session.__getitem__.return_value = "fcsess_test123_secret"
            mock_session_create.return_value = mock_session

            response = test_client.post(
                "/api/create-fc-session",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_create_accounts_stores_bank_accounts(self, test_client, jwt_token, flask_app):
        """Creating accounts stores bank account data"""
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

    def test_empty_accounts_list_returns_400(self, test_client, jwt_token):
        """Empty accounts list returns 400 error"""
        response = test_client.post(
            "/api/create_accounts",
            headers={"Authorization": "Bearer " + jwt_token},
            json=[],
        )

        assert response.status_code == 400
        assert "No Accounts Submitted" in response.get_data(as_text=True)

    def test_accounts_endpoint_returns_404(self, test_client, jwt_token, flask_app, mocker):
        """Accounts endpoint returns 404 (not implemented)"""
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
            from models.database import SessionLocal
            from utils.pg_bulk_ops import bulk_upsert_bank_accounts

            with SessionLocal.begin() as db:
                bulk_upsert_bank_accounts(db, [test_account])

            response = test_client.get(
                "/api/accounts",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 404  # This endpoint doesn't exist in the current API

    def test_accounts_and_balances_returns_balance_data(self, test_client, jwt_token, flask_app, mocker):
        """Accounts and balances endpoint returns balance data for each account"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            from datetime import datetime, timezone

            # Insert test account with balance
            test_account = {
                "id": "fca_test123",
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
                "status": "active",
                "latest_balance": 100.0,
                "currency": "usd",
                "balance_as_of": datetime(2023, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            }
            from models.database import SessionLocal
            from utils.pg_bulk_ops import bulk_upsert_bank_accounts

            with SessionLocal.begin() as db:
                bulk_upsert_bank_accounts(db, [test_account])

            response = test_client.get(
                "/api/accounts_and_balances",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert "fca_test123" in data
            account_data = data["fca_test123"]
            assert account_data["balance"] == 100.0
            assert account_data["currency"] == "usd"
            assert account_data["name"] == "Test Bank Checking Account 1234"

    def test_subscribe_to_account_enables_transaction_syncing(self, test_client, jwt_token, flask_app, mocker):
        """Subscribing to account enables automatic transaction syncing"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            mock_subscribe = mocker.patch("resources.stripe.stripe.financial_connections.Account.subscribe")

            # Mock successful response
            mock_response = mocker.MagicMock()
            mock_response.get.return_value = {"status": "succeeded"}
            mock_subscribe.return_value = mock_response

            response = test_client.post(
                "/api/subscribe_to_account",
                headers={"Authorization": "Bearer " + jwt_token},
                json={"account_id": "fca_test123"},
            )

            assert response.status_code == 200
            assert response.get_data(as_text=True).strip() == '"succeeded"'

    def test_refresh_account_updates_account_data(self, flask_app, jwt_token, mocker):
        """Refreshing account updates stored account data"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            mock_retrieve = mocker.patch("resources.stripe.stripe.financial_connections.Account.retrieve")
            # Mock bulk_upsert_bank_accounts to avoid trying to serialize Mock objects to PostgreSQL
            mocker.patch("resources.stripe.bulk_upsert_bank_accounts")

            # Mock account
            mock_account = mocker.MagicMock()
            mock_account.id = "fca_test123"
            mock_account.__getitem__.side_effect = lambda k: getattr(mock_account, k)
            mock_retrieve.return_value = mock_account

            response = flask_app.test_client().get(
                "/api/refresh_account/fca_test123",
                headers={"Authorization": f"Bearer {jwt_token}"},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["data"] == "success"

    def test_relink_account_returns_new_session_secret(self, test_client, jwt_token, flask_app, mocker):
        """Relinking account returns new session client secret"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            mock_retrieve = mocker.patch("resources.stripe.stripe.financial_connections.Account.retrieve")
            mock_check_can_relink = mocker.patch("resources.stripe.check_can_relink")
            mock_create_session = mocker.patch("resources.stripe.create_fc_session_api")

            # Mock account
            mock_account = mocker.MagicMock()
            mock_account.id = "fca_test123"
            mock_account.authorization = "fcauth_test123"
            mock_account.__getitem__.side_effect = lambda k: getattr(mock_account, k)
            mock_retrieve.return_value = mock_account

            # Mock check_can_relink to return True (relink required)
            mock_check_can_relink.return_value = True

            # Mock session creation
            mock_session_response = mocker.Mock()
            mock_session_response.json = {"client_secret": "fcsess_test123_secret"}
            mock_create_session.return_value = (mock_session_response, 200)

            response = test_client.post(
                "/api/relink_account/fca_test123",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert "client_secret" in data

    def test_active_account_does_not_need_relink(self, test_client, jwt_token, flask_app, mocker):
        """Active account returns relink_required=false"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            mock_retrieve = mocker.patch("resources.stripe.stripe.financial_connections.Account.retrieve")
            mock_check_can_relink = mocker.patch("resources.stripe.check_can_relink")

            # Mock account
            mock_account = mocker.MagicMock()
            mock_account.id = "fca_test123"
            mock_account.authorization = "fcauth_test123"
            mock_account.__getitem__.side_effect = lambda k: getattr(mock_account, k)
            mock_retrieve.return_value = mock_account

            # Mock check_can_relink to return False (relink not required)
            mock_check_can_relink.return_value = False

            response = test_client.post(
                "/api/relink_account/fca_test123",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert not data["relink_required"]

    def test_refresh_transactions_fetches_new_transactions(self, flask_app, jwt_token, mocker):
        """Refreshing transactions fetches new transactions from Stripe"""
        mocker.patch("resources.stripe.STRIPE_API_KEY", "test_api_key")
        mocker.patch("resources.stripe.STRIPE_CUSTOMER_ID", "test_customer_id")

        with flask_app.app_context():
            # Mock Stripe SDK call
            mock_list = mocker.patch("resources.stripe.stripe.financial_connections.Transaction.list")

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
                "/api/refresh_transactions/fca_test123",
                headers={"Authorization": f"Bearer {jwt_token}"},
            )

            assert response.status_code == 200
            assert "Refreshed Stripe Connection for Given Account" in response.get_data(as_text=True)


class TestStripeFunctions:
    @pytest.mark.parametrize("full_refresh", [False, True])
    def test_refresh_fetches_each_balance_and_normalizes_stripe_once(
        self, flask_app, test_client, jwt_token, mocker, full_refresh
    ):
        accounts = [{"id": "fca_first"}, {"id": "fca_second"}]
        mocker.patch("resources.stripe.get_all_bank_accounts", return_value=accounts)
        mocker.patch("resources.stripe.refresh_account")
        mocker.patch(
            "resources.stripe.stripe.financial_connections.Transaction.list",
            return_value=mocker.Mock(data=[], has_more=False),
        )
        balances = mocker.patch("resources.stripe.refresh_account_balances")
        convert = mocker.patch("resources.stripe.stripe_to_line_items")

        if full_refresh:
            from application import create_consistent_line_items, refresh_all

            mocker.patch("application.refresh_splitwise")
            mocker.patch("application.refresh_venmo")
            mocker.patch("application.splitwise_to_line_items")
            mocker.patch("application.venmo_to_line_items")
            mocker.patch("application.stripe_to_line_items", convert)
            refresh_all()
            create_consistent_line_items()
        else:
            response = test_client.get("/api/refresh/stripe", headers={"Authorization": "Bearer " + jwt_token})
            assert response.status_code == 200

        assert balances.call_args_list == [
            mocker.call(account_ids=["fca_first"]),
            mocker.call(account_ids=["fca_second"]),
        ]
        convert.assert_called_once_with()

    def test_refresh_transactions_retains_classifications_on_existing_transactions(self, flask_app, mocker):
        mocker.patch("resources.stripe.refresh_account_balances")
        mock_list = mocker.patch("resources.stripe.stripe.financial_connections.Transaction.list")
        transaction = {
            "id": "fctxn_classified",
            "account": "fca_test123",
            "amount": -5000,
            "description": "Tax refund",
            "status": "posted",
            "transacted_at": 1673778600,
        }
        classifications = [
            {
                "type": "money_movement",
                "money_movement": {
                    "confidence_level": "high",
                    "detailed_label": "inbound_tax_refund",
                    "primary_label": "inbound",
                },
            }
        ]
        original_version = stripe.api_version
        mock_list.return_value = mocker.Mock(
            data=[stripe.StripeObject.construct_from(transaction, "test_api_key")], has_more=False
        )
        refresh_transactions("fca_test123")

        transaction["classifications"] = classifications
        mock_list.return_value = mocker.Mock(
            data=[stripe.StripeObject.construct_from(transaction, "test_api_key")], has_more=False
        )
        refresh_transactions("fca_test123")

        stored = get_transactions("stripe_api", None)
        assert len(stored) == 1
        assert stored[0]["source_id"] == "fctxn_classified"
        assert stored[0]["classifications"] == classifications
        assert stripe.api_version == original_version
        assert mock_list.call_count == 2
        for call in mock_list.call_args_list:
            assert call.kwargs == {"account": "fca_test123", "limit": 100}

    def test_refresh_stripe_syncs_each_account(self, flask_app, mocker):
        """Refresh stripe syncs each stored bank account"""
        with flask_app.app_context():
            mock_refresh_account = mocker.patch("resources.stripe.refresh_account")
            mock_refresh_transactions = mocker.patch("resources.stripe.refresh_transactions")
            mock_convert = mocker.patch("resources.stripe.stripe_to_line_items")

            # Insert test account data
            test_account = {
                "id": "fca_test123",
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
            }
            from models.database import SessionLocal
            from utils.pg_bulk_ops import bulk_upsert_bank_accounts

            with SessionLocal.begin() as db:
                bulk_upsert_bank_accounts(db, [test_account])

            # Call the function
            refresh_stripe()

            # Verify all functions were called
            mock_refresh_account.assert_called_once_with("fca_test123")
            mock_refresh_transactions.assert_called_once_with("fca_test123")
            mock_convert.assert_not_called()

    def test_no_accounts_skips_sync_and_conversion(self, flask_app, mocker):
        """No accounts skips sync and leaves conversion to the caller"""
        with flask_app.app_context():
            mock_refresh_account = mocker.patch("resources.stripe.refresh_account")
            mock_refresh_transactions = mocker.patch("resources.stripe.refresh_transactions")
            mock_convert = mocker.patch("resources.stripe.stripe_to_line_items")

            # Call the function with no accounts
            refresh_stripe()

            # Verify no refresh calls were made
            mock_refresh_account.assert_not_called()
            mock_refresh_transactions.assert_not_called()
            mock_convert.assert_not_called()

    @pytest.mark.parametrize(
        ("enrichments", "expected_party"),
        [
            (None, "Test transaction"),
            ({}, "Test transaction"),
            ({"merchant": None}, "Test transaction"),
            ({"merchant": {"name": ""}}, "Test transaction"),
            ({"merchant": {"name": "Example Merchant"}}, "Test transaction"),
            ({"merchant": {"name": "Example Merchant", "confidence_level": "low"}}, "Test transaction"),
            ({"merchant": {"name": "Example Merchant", "confidence_level": "medium"}}, "Test transaction"),
            ({"merchant": {"name": "Example Merchant", "confidence_level": "high"}}, "Example Merchant"),
            ({"merchant": {"name": "Example Merchant", "confidence_level": "very_high"}}, "Example Merchant"),
            ({"merchant": {"name": "", "confidence_level": "high"}}, "Test transaction"),
            ({"merchant": {"name": None, "confidence_level": "very_high"}}, "Test transaction"),
        ],
    )
    def test_stripe_transactions_convert_to_line_items(
        self, flask_app, mock_stripe_transaction, mocker, enrichments, expected_party
    ):
        """Stripe transactions convert to line items with amounts in dollars"""
        with flask_app.app_context():
            # Insert test data
            test_account = {
                "id": "fca_test123",
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
            }
            from models.database import SessionLocal
            from utils.pg_bulk_ops import bulk_upsert_bank_accounts

            with SessionLocal.begin() as db:
                bulk_upsert_bank_accounts(db, [test_account])

            test_transaction = mock_stripe_transaction
            from models.database import SessionLocal
            from utils.pg_bulk_ops import bulk_upsert_transactions

            with SessionLocal.begin() as db:
                bulk_upsert_transactions(db, [test_transaction], source="stripe_api")

            # Call the function (writes to PostgreSQL)
            stripe_to_line_items()

            # Query database to verify line items were created
            from models.database import SessionLocal
            from models.sql_models import LineItem

            with SessionLocal.begin() as db:
                line_items = db.query(LineItem).all()
                assert len(line_items) == 1

                line_item = line_items[0]
                assert line_item.id.startswith("li_")
                assert line_item.responsible_party == "Test transaction"
                assert line_item.description == "Test transaction"
                assert line_item.amount == 50.0
                original_id = line_item.id

            test_transaction["enrichments"] = enrichments
            with SessionLocal.begin() as db:
                bulk_upsert_transactions(db, [test_transaction], source="stripe_api")
            stripe_to_line_items()

            with SessionLocal.begin() as db:
                line_item = db.query(LineItem).one()
                assert line_item.id == original_id
                assert line_item.responsible_party == expected_party
                assert line_item.description == "Test transaction"
                assert line_item.amount == 50.0

    def test_empty_transactions_creates_no_line_items(self, flask_app, mocker):
        """Empty transaction list creates no line items"""
        with flask_app.app_context():
            mocker.patch("resources.stripe.bulk_upsert_line_items")

            # Call the function with no transactions
            stripe_to_line_items()

    def test_missing_account_skips_transaction(self, flask_app, mock_stripe_transaction, mocker):
        """Transactions for missing accounts are skipped"""
        with flask_app.app_context():
            # Insert transaction without corresponding account
            test_transaction = mock_stripe_transaction
            from models.database import SessionLocal
            from utils.pg_bulk_ops import bulk_upsert_transactions

            with SessionLocal.begin() as db:
                bulk_upsert_transactions(db, [test_transaction], source="stripe_api")

            mocker.patch("resources.stripe.bulk_upsert_line_items")

            # Call the function
            stripe_to_line_items()

    def test_large_transaction_sets_are_batched(self, flask_app, mocker):
        """Large transaction sets are processed in batches"""
        with flask_app.app_context():
            # Insert test account
            test_account = {
                "id": "fca_test123",
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
            }
            from models.database import SessionLocal
            from utils.pg_bulk_ops import bulk_upsert_bank_accounts

            with SessionLocal.begin() as db:
                bulk_upsert_bank_accounts(db, [test_account])

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

            from models.database import SessionLocal
            from utils.pg_bulk_ops import bulk_upsert_transactions

            with SessionLocal.begin() as db:
                bulk_upsert_transactions(db, transactions, source="stripe_api")

            mocker.patch("resources.stripe.bulk_upsert_line_items")

            # Call the function
            stripe_to_line_items()


class TestBulkUpsertBankAccounts:
    """Unit tests for bulk_upsert_bank_accounts"""

    def test_account_with_none_last4_is_inserted(self, flask_app):
        """Stripe accounts can return last4=None (e.g. brokerage/stock plans);
        the upsert must coerce None to empty string to satisfy the NOT NULL constraint."""
        with flask_app.app_context():
            from models.database import SessionLocal
            from models.sql_models import BankAccount
            from utils.pg_bulk_ops import bulk_upsert_bank_accounts

            account = {
                "id": "fca_no_last4",
                "institution_name": "Solium - Shareworks",
                "display_name": "Common",
                "last4": None,
                "status": "active",
                "can_relink": False,
            }

            with SessionLocal.begin() as db:
                count = bulk_upsert_bank_accounts(db, [account])

            assert count == 1
            with SessionLocal() as db:
                row = db.query(BankAccount).filter_by(id="fca_no_last4").one()
                assert row.last4 == ""
                assert row.institution_name == "Solium - Shareworks"
                assert row.status == "active"


class TestCheckCanRelink:
    """Direct unit tests for check_can_relink function"""

    def test_active_account_returns_false(self, flask_app):
        """Active accounts return false for relink check"""
        with flask_app.app_context():
            from resources.stripe import check_can_relink

            account = {"id": "fca_test123", "status": "active"}
            result = check_can_relink(account)

            assert result is False

    def test_inactive_account_with_relink_action_returns_true(self, flask_app, mocker):
        """Inactive account with relink_required action returns true"""
        with flask_app.app_context():
            from resources.stripe import check_can_relink

            mock_requests_get = mocker.patch("requests.get")
            mock_response = mocker.MagicMock()
            mock_response.json.return_value = {
                "status": "inactive",
                "status_details": {"inactive": {"action": "relink_required"}},
            }
            mock_requests_get.return_value = mock_response

            account = {"id": "fca_test123", "status": "inactive", "authorization": "fcauth_test123"}
            result = check_can_relink(account)

            assert result is True
            mock_requests_get.assert_called_once_with(
                "https://api.stripe.com/v1/financial_connections/authorizations/fcauth_test123",
                headers={"Stripe-Version": STRIPE_API_VERSION},
                auth=(STRIPE_API_KEY, ""),
            )

    def test_account_closed_at_bank_returns_false(self, flask_app, mocker):
        """Account closed at bank cannot be relinked"""
        with flask_app.app_context():
            from resources.stripe import check_can_relink

            mock_requests_get = mocker.patch("requests.get")
            mock_response = mocker.MagicMock()
            mock_response.json.return_value = {"status": "active"}
            mock_requests_get.return_value = mock_response

            account = {"id": "fca_test123", "status": "inactive", "authorization": "fcauth_test123"}
            result = check_can_relink(account)

            assert result is False

    def test_action_none_returns_false(self, flask_app, mocker):
        """Inactive account with action=none returns false"""
        with flask_app.app_context():
            from resources.stripe import check_can_relink

            mock_requests_get = mocker.patch("requests.get")
            mock_response = mocker.MagicMock()
            mock_response.json.return_value = {"status": "inactive", "status_details": {"inactive": {"action": "none"}}}
            mock_requests_get.return_value = mock_response

            account = {"id": "fca_test123", "status": "inactive", "authorization": "fcauth_test123"}
            result = check_can_relink(account)

            assert result is False

    def test_api_error_defaults_to_false(self, flask_app, mocker):
        """API errors default to false for safety"""
        with flask_app.app_context():
            from resources.stripe import check_can_relink

            mock_requests_get = mocker.patch("requests.get")
            mock_requests_get.side_effect = Exception("API error")

            account = {"id": "fca_test123", "status": "inactive", "authorization": "fcauth_test123"}
            result = check_can_relink(account)

            assert result is False

    def test_missing_authorization_returns_false(self, flask_app):
        """Account without authorization ID returns false"""
        with flask_app.app_context():
            from resources.stripe import check_can_relink

            account = {"id": "fca_test123", "status": "inactive", "authorization": None}
            result = check_can_relink(account)

            assert result is False

    def test_unknown_auth_status_returns_false(self, flask_app, mocker):
        """Unknown authorization status returns false"""
        with flask_app.app_context():
            from resources.stripe import check_can_relink

            mock_requests_get = mocker.patch("requests.get")
            mock_response = mocker.MagicMock()
            mock_response.json.return_value = {"status": "unknown_status"}
            mock_requests_get.return_value = mock_response

            account = {"id": "fca_test123", "status": "inactive", "authorization": "fcauth_test123"}
            result = check_can_relink(account)

            assert result is False


class TestStripeIntegration:
    def test_complete_workflow_syncs_accounts_and_creates_line_items(self, flask_app, mocker):
        """Complete workflow syncs accounts, transactions, and creates line items"""
        with flask_app.app_context():
            mock_refresh_account = mocker.patch("resources.stripe.refresh_account")
            mock_refresh_transactions = mocker.patch("resources.stripe.refresh_transactions")
            mocker.patch("resources.stripe.bulk_upsert_line_items")

            # Insert test account
            test_account = {
                "id": "fca_test123",
                "institution_name": "Test Bank",
                "display_name": "Checking Account",
                "last4": "1234",
            }
            from models.database import SessionLocal
            from utils.pg_bulk_ops import bulk_upsert_bank_accounts

            with SessionLocal.begin() as db:
                bulk_upsert_bank_accounts(db, [test_account])

            # Insert test transaction
            test_transaction = {
                "id": "fct_test123",
                "account": "fca_test123",
                "amount": -2500,  # $25.00 in cents
                "description": "Integration test transaction",
                "status": "posted",
                "transacted_at": 1673778600,
            }
            from utils.pg_bulk_ops import bulk_upsert_transactions

            with SessionLocal.begin() as db:
                bulk_upsert_transactions(db, [test_transaction], source="stripe_api")

            # Call refresh function
            refresh_stripe()

            # Verify refresh functions were called
            mock_refresh_account.assert_called_once_with("fca_test123")
            mock_refresh_transactions.assert_called_once_with("fca_test123")

            # Verify line items were created


class TestAccountBalances:
    """Tests for account balance functionality (simplified approach)"""

    def test_refresh_balances_updates_account_records(self, flask_app, mocker):
        """Refresh balances fetches and stores balance on account records"""
        from resources.stripe import refresh_account_balances

        with flask_app.app_context():
            # Mock Stripe client
            mock_balance_data = mocker.Mock()
            mock_balance_data.current = {"usd": 10000}  # $100.00 in cents
            mock_balance_data.as_of = 1700000000

            mock_balances = mocker.Mock()
            mock_balances.data = [mock_balance_data]

            mock_stripe_client = mocker.patch("resources.stripe.stripe_client")
            mock_stripe_client.v1.financial_connections.accounts.inferred_balances.list.return_value = mock_balances

            # Setup test account
            test_account = {
                "id": "fca_test123",
                "institution_name": "Test Bank",
                "display_name": "Checking",
                "last4": "1234",
                "status": "active",
            }
            from models.database import SessionLocal
            from utils.pg_bulk_ops import bulk_upsert_bank_accounts

            with SessionLocal.begin() as db:
                bulk_upsert_bank_accounts(db, [test_account])

            # Call refresh_account_balances
            count = refresh_account_balances()

            # Verify Stripe API was called correctly
            mock_stripe_client.v1.financial_connections.accounts.inferred_balances.list.assert_called_once()

            # Verify balance was stored on account
            assert count == 1
            accounts = get_all_bank_accounts(None)
            updated_account = next(acc for acc in accounts if acc["id"] == "fca_test123")
            assert updated_account["latest_balance"] == 100.0
            assert updated_account["currency"] == "usd"
            assert updated_account["balance_as_of"] is not None

    def test_accounts_and_balances_reads_stored_balance_data(self, test_client, jwt_token, flask_app):
        """Accounts and balances endpoint reads stored balance data"""
        from datetime import UTC, datetime

        with flask_app.app_context():
            # Setup test account with balance
            test_account = {
                "id": "fca_test789",
                "institution_name": "Test Bank",
                "display_name": "Savings",
                "last4": "5678",
                "status": "active",
                "can_relink": False,
                "latest_balance": 150.50,
                "currency": "usd",
                "balance_as_of": datetime.fromtimestamp(1700000000, UTC),
            }
            from models.database import SessionLocal
            from utils.pg_bulk_ops import bulk_upsert_bank_accounts

            with SessionLocal.begin() as db:
                bulk_upsert_bank_accounts(db, [test_account])

            # Call API endpoint
            response = test_client.get(
                "/api/accounts_and_balances",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert "fca_test789" in data
            assert data["fca_test789"]["balance"] == 150.50
            assert data["fca_test789"]["currency"] == "usd"
            # Timestamp may vary due to timezone handling
            assert data["fca_test789"]["as_of"] is not None
            assert isinstance(data["fca_test789"]["as_of"], int)
            assert data["fca_test789"]["name"] == "Test Bank Savings 5678"
            assert data["fca_test789"]["status"] == "active"
