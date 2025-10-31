import os

import pytest

# Set up fake environment variables for testing before any imports
if "VENMO_ACCESS_TOKEN" not in os.environ:
    os.environ["VENMO_ACCESS_TOKEN"] = "fake_token_for_testing"
if "STRIPE_LIVE_API_SECRET_KEY" not in os.environ:
    os.environ["STRIPE_LIVE_API_SECRET_KEY"] = "fake_stripe_key_for_testing"
if "STRIPE_CUSTOMER_ID" not in os.environ:
    os.environ["STRIPE_CUSTOMER_ID"] = "fake_customer_id_for_testing"

import mongomock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from constants import JWT_SECRET_KEY
from dao import (
    bank_accounts_collection,
    cash_raw_data_collection,
    events_collection,
    line_items_collection,
    splitwise_raw_data_collection,
    stripe_raw_account_data_collection,
    stripe_raw_transaction_data_collection,
    test_collection,
    users_collection,
    venmo_raw_data_collection,
)
from resources.auth import auth_blueprint
from resources.cash import cash_blueprint
from resources.event import events_blueprint
from resources.line_item import line_items_blueprint
from resources.monthly_breakdown import monthly_breakdown_blueprint
from resources.splitwise import splitwise_blueprint
from resources.stripe import stripe_blueprint
from resources.venmo import venmo_blueprint

# Import test configuration
try:
    from test_config import TEST_DB_NAME, TEST_MONGO_URI
except ImportError:
    # Fallback if test_config doesn't exist
    TEST_MONGO_URI = os.getenv(
        "TEST_MONGO_URI", "mongodb://localhost:27017/budgit_test"
    )
    TEST_DB_NAME = "budgit_test"


@pytest.fixture
def flask_app():
    app = Flask(__name__)
    app.debug = True
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(cash_blueprint)
    app.register_blueprint(line_items_blueprint)
    app.register_blueprint(events_blueprint)
    app.register_blueprint(monthly_breakdown_blueprint)
    app.register_blueprint(splitwise_blueprint)
    app.register_blueprint(stripe_blueprint)
    app.register_blueprint(venmo_blueprint)

    # Use a separate test database
    app.config["MONGO_URI"] = TEST_MONGO_URI
    app.config["MONGO_DB_NAME"] = TEST_DB_NAME

    with app.app_context():
        # Use mongomock for testing - no real MongoDB server required
        mongo_client = mongomock.MongoClient()

        # Create a mock MongoDB object that mimics PyMongo's structure
        class MockMongo:
            def __init__(self, client):
                self.cx = client

        app.config["MONGO"] = MockMongo(mongo_client)
        jwt = JWTManager(app)
        app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY

        # Add user lookup loader for JWT
        @jwt.user_lookup_loader
        def user_lookup_callback(jwt_header, jwt_payload):
            return {"email": "test@example.com", "id": "user_id"}

        # Import and register main application routes from application.py
        from application import (
            get_connected_accounts_api,
            get_payment_methods_api,
            index_api,
            refresh_all_api,
            schedule_refresh_api,
        )

        app.add_url_rule("/api/", "index_api", index_api, methods=["GET"])
        app.add_url_rule(
            "/api/refresh/scheduled",
            "schedule_refresh_api",
            schedule_refresh_api,
            methods=["GET"],
        )
        app.add_url_rule(
            "/api/refresh/all", "refresh_all_api", refresh_all_api, methods=["GET"]
        )
        app.add_url_rule(
            "/api/connected_accounts",
            "get_connected_accounts_api",
            get_connected_accounts_api,
            methods=["GET"],
        )
        app.add_url_rule(
            "/api/payment_methods",
            "get_payment_methods_api",
            get_payment_methods_api,
            methods=["GET"],
        )

    yield app


@pytest.fixture
def test_client(flask_app):
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def jwt_token(flask_app):
    with flask_app.app_context():
        token = create_access_token(identity="user_id")
    return token


@pytest.fixture(autouse=True)
def setup_teardown(flask_app, request):
    # This fixture will be used for setup and teardown
    with flask_app.app_context():
        # Get the test database
        test_db = flask_app.config["MONGO"].cx[flask_app.config["MONGO_DB_NAME"]]

        # Clean up collections before each test
        test_db.drop_collection(test_collection)
        test_db.drop_collection(cash_raw_data_collection)
        test_db.drop_collection(line_items_collection)
        test_db.drop_collection(splitwise_raw_data_collection)
        test_db.drop_collection(stripe_raw_account_data_collection)
        test_db.drop_collection(stripe_raw_transaction_data_collection)
        test_db.drop_collection(bank_accounts_collection)
        test_db.drop_collection(events_collection)
        test_db.drop_collection(users_collection)
        test_db.drop_collection(venmo_raw_data_collection)

    def teardown():
        with flask_app.app_context():
            # Get the test database
            test_db = flask_app.config["MONGO"].cx[flask_app.config["MONGO_DB_NAME"]]

            # Clean up collections after each test
            test_db.drop_collection(test_collection)
            test_db.drop_collection(cash_raw_data_collection)
            test_db.drop_collection(line_items_collection)
            test_db.drop_collection(splitwise_raw_data_collection)
            test_db.drop_collection(stripe_raw_account_data_collection)
            test_db.drop_collection(stripe_raw_transaction_data_collection)
            test_db.drop_collection(bank_accounts_collection)
            test_db.drop_collection(events_collection)
            test_db.drop_collection(users_collection)
            test_db.drop_collection(venmo_raw_data_collection)

    request.addfinalizer(teardown)
