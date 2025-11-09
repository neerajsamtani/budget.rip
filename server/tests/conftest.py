import os

import pytest

# Set up fake environment variables for testing before any imports
if "VENMO_ACCESS_TOKEN" not in os.environ:
    os.environ["VENMO_ACCESS_TOKEN"] = "fake_token_for_testing"
if "STRIPE_LIVE_API_SECRET_KEY" not in os.environ:
    os.environ["STRIPE_LIVE_API_SECRET_KEY"] = "fake_stripe_key_for_testing"
if "STRIPE_CUSTOMER_ID" not in os.environ:
    os.environ["STRIPE_CUSTOMER_ID"] = "fake_customer_id_for_testing"

# CRITICAL: Set test database URL to SQLite shared in-memory BEFORE any imports
# This prevents test data from polluting the production PostgreSQL database
# Using shared memory mode allows multiple engine connections to access the same database
os.environ["DATABASE_URL"] = "sqlite:///file:memdb1?mode=memory&cache=shared&uri=true"

import mongomock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

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
from models.sql_models import Base
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
    TEST_MONGO_URI = os.getenv("TEST_MONGO_URI", "mongodb://localhost:27017/budgit_test")
    TEST_DB_NAME = "budgit_test"


# Global test database engine and session
TEST_DATABASE_URL = os.environ["DATABASE_URL"]
test_engine = None
TestSession = None


def init_test_db():
    """Initialize the test database schema"""
    global test_engine, TestSession
    # Enable URI mode for SQLite to support shared memory connections
    test_engine = create_engine(TEST_DATABASE_URL, echo=False, connect_args={"uri": True})

    # Enable foreign key constraints for SQLite
    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestSession = sessionmaker(bind=test_engine)

    # Create all tables
    Base.metadata.create_all(test_engine)

    return test_engine


def cleanup_test_db():
    """Clean up all tables in the test database"""
    if test_engine is not None:
        # Drop all tables
        Base.metadata.drop_all(test_engine)
        # Recreate them for the next test
        Base.metadata.create_all(test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up the test database once for the entire test session"""
    init_test_db()
    yield
    # Final cleanup after all tests
    if test_engine is not None:
        Base.metadata.drop_all(test_engine)
        test_engine.dispose()


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
        app.add_url_rule("/api/refresh/all", "refresh_all_api", refresh_all_api, methods=["GET"])
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


@pytest.fixture
def pg_session():
    """Provide a SQLite session using the shared test database"""
    if TestSession is None:
        init_test_db()

    session = TestSession()
    yield session
    session.rollback()  # Rollback any uncommitted changes
    session.close()


def seed_postgresql_base_data():
    """Seed PostgreSQL with required base data (categories, payment methods)"""
    from models.sql_models import Category, PaymentMethod

    session = TestSession()
    try:
        categories = [
            {"id": "cat_all", "name": "All"},
            {"id": "cat_alcohol", "name": "Alcohol"},
            {"id": "cat_dining", "name": "Dining"},
            {"id": "cat_entertainment", "name": "Entertainment"},
            {"id": "cat_forma", "name": "Forma"},
            {"id": "cat_groceries", "name": "Groceries"},
            {"id": "cat_hobbies", "name": "Hobbies"},
            {"id": "cat_income", "name": "Income"},
            {"id": "cat_investment", "name": "Investment"},
            {"id": "cat_medical", "name": "Medical"},
            {"id": "cat_rent", "name": "Rent"},
            {"id": "cat_shopping", "name": "Shopping"},
            {"id": "cat_subscription", "name": "Subscription"},
            {"id": "cat_transfer", "name": "Transfer"},
            {"id": "cat_transit", "name": "Transit"},
            {"id": "cat_travel", "name": "Travel"},
            {"id": "cat_food", "name": "Food"},
            {"id": "cat_transportation", "name": "Transportation"},
        ]
        for cat_data in categories:
            if not session.query(Category).filter_by(name=cat_data["name"]).first():
                session.add(Category(**cat_data))

        payment_methods = [
            {"id": "pm_cash", "name": "Cash", "type": "cash", "is_active": True},
            {"id": "pm_venmo", "name": "Venmo", "type": "venmo", "is_active": True},
            {
                "id": "pm_splitwise",
                "name": "Splitwise",
                "type": "splitwise",
                "is_active": True,
            },
            {
                "id": "pm_credit_card",
                "name": "Credit Card",
                "type": "credit",
                "is_active": True,
            },
            {
                "id": "pm_debit_card",
                "name": "Debit Card",
                "type": "bank",
                "is_active": True,
            },
        ]
        for pm_data in payment_methods:
            if not session.query(PaymentMethod).filter_by(name=pm_data["name"]).first():
                session.add(PaymentMethod(**pm_data))

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture(autouse=True)
def setup_teardown(flask_app, request):
    # This fixture will be used for setup and teardown
    with flask_app.app_context():
        # Clean up MongoDB collections before each test
        test_db = flask_app.config["MONGO"].cx[flask_app.config["MONGO_DB_NAME"]]
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

        # Clean up PostgreSQL tables before each test
        cleanup_test_db()

        # Seed PostgreSQL with base data if READ_FROM_POSTGRESQL=true
        # Skip for phase5 tests as they have their own fixtures
        if "test_phase5" not in request.node.fspath.basename:
            seed_postgresql_base_data()

    def teardown():
        with flask_app.app_context():
            # Clean up MongoDB collections after each test
            test_db = flask_app.config["MONGO"].cx[flask_app.config["MONGO_DB_NAME"]]
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

            # Clean up PostgreSQL tables after each test
            cleanup_test_db()

    request.addfinalizer(teardown)


@pytest.fixture
def create_line_item_via_cash(test_client, jwt_token):
    """Helper to create line items via cash transaction API"""

    def _create(**kwargs):
        transaction_data = {
            "date": kwargs.get("date", "2009-02-13"),
            "person": kwargs.get("person", "Test Person"),
            "description": kwargs.get("description", "Test Transaction"),
            "amount": kwargs.get("amount", 100.0),
        }
        response = test_client.post(
            "/api/cash_transaction",
            json=transaction_data,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 201
        return transaction_data

    return _create


@pytest.fixture
def create_event_via_api(test_client, jwt_token):
    """Helper to create events via API"""

    def _create(event_data):
        response = test_client.post(
            "/api/events",
            json=event_data,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 201
        return response.get_json()

    return _create


@pytest.fixture
def create_user_via_api(test_client):
    """Helper to create users via signup API"""

    def _create(user_data):
        response = test_client.post(
            "/api/auth/signup",
            json=user_data,
        )
        assert response.status_code == 201
        return response.get_json()

    return _create
