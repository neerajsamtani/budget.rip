import os

import pytest

# Set up fake environment variables for testing before any imports
test_env_vars = {
    "JWT_SECRET_KEY": "testSecretKey123",
    "JWT_COOKIE_DOMAIN": "localhost",
    "VENMO_ACCESS_TOKEN": "fake_token_for_testing",
    "STRIPE_LIVE_API_SECRET_KEY": "fake_stripe_key_for_testing",
    "STRIPE_CUSTOMER_ID": "fake_customer_id_for_testing",
    "SPLITWISE_CONSUMER_KEY": "fake_splitwise_key",
    "SPLITWISE_CONSUMER_SECRET": "fake_splitwise_secret",
    "SPLITWISE_API_KEY": "fake_splitwise_api_key",
}
for key, value in test_env_vars.items():
    if key not in os.environ:
        os.environ[key] = value

# CRITICAL: Set test environment BEFORE any imports
# This prevents test data from polluting the production PostgreSQL database
os.environ["TESTING"] = "true"
os.environ["DATABASE_HOST"] = "sqlite"
# Use a unique name for the shared in-memory database to avoid file creation
os.environ["DATABASE_NAME"] = ":memory:"

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from constants import JWT_SECRET_KEY
from models.sql_models import Base
from resources.auth import auth_blueprint
from resources.cash import cash_blueprint
from resources.category import categories_blueprint
from resources.event import events_blueprint
from resources.event_hint import event_hints_blueprint
from resources.line_item import line_items_blueprint
from resources.monthly_breakdown import monthly_breakdown_blueprint
from resources.splitwise import splitwise_blueprint
from resources.stripe import stripe_blueprint
from resources.tags import tags_blueprint
from resources.venmo import venmo_blueprint

# Global test database engine and session
test_engine = None
TestSession = None


def init_test_db():
    """Initialize the test database schema"""
    global test_engine, TestSession
    import sqlite3

    # Use a shared in-memory database via a creator function
    # This avoids SQLite creating physical files with names like "file:memdb1"
    def get_shared_memory_connection():
        return sqlite3.connect("file::memory:?cache=shared", uri=True)

    test_engine = create_engine(
        "sqlite://",
        creator=get_shared_memory_connection,
        echo=False,
    )

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
    else:
        # If test_engine not initialized yet, initialize it first
        init_test_db()
        Base.metadata.drop_all(test_engine)
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
    app.register_blueprint(categories_blueprint)
    app.register_blueprint(event_hints_blueprint)
    app.register_blueprint(line_items_blueprint)
    app.register_blueprint(events_blueprint)
    app.register_blueprint(monthly_breakdown_blueprint)
    app.register_blueprint(splitwise_blueprint)
    app.register_blueprint(stripe_blueprint)
    app.register_blueprint(tags_blueprint)
    app.register_blueprint(venmo_blueprint)

    with app.app_context():
        jwt = JWTManager(app)
        app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
        app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
        app.config["JWT_ACCESS_COOKIE_PATH"] = "/api/"
        app.config["JWT_COOKIE_CSRF_PROTECT"] = False  # Disable CSRF for tests
        app.config["JWT_COOKIE_SECURE"] = False  # Allow non-HTTPS in tests

        # Add user lookup loader for JWT
        @jwt.user_lookup_loader
        def user_lookup_callback(jwt_header, jwt_payload):
            user_id = jwt_payload.get("sub")
            if user_id:
                # Query PostgreSQL using the dao layer
                from dao import get_item_by_id, users_collection

                user = get_item_by_id(users_collection, user_id)
                if user:
                    return user
            # Fallback for tests that use the old jwt_token fixture
            return {"email": "test@example.com", "id": "user_id"}

        # Import and register main application routes from application.py
        from application import (
            get_connected_accounts_api,
            get_payment_methods_api,
            index_api,
            refresh_all_api,
            refresh_single_account_api,
            schedule_refresh_api,
        )

        app.add_url_rule("/api/", "index_api", index_api, methods=["GET"])
        app.add_url_rule(
            "/api/refresh/scheduled",
            "schedule_refresh_api",
            schedule_refresh_api,
            methods=["GET"],
        )
        app.add_url_rule("/api/refresh/all", "refresh_all_api", refresh_all_api, methods=["POST"])
        app.add_url_rule(
            "/api/refresh/account",
            "refresh_single_account_api",
            refresh_single_account_api,
            methods=["POST"],
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
    """Seed PostgreSQL with required base data (categories, payment methods) for test user"""
    from models.sql_models import Category, PaymentMethod, User

    session = TestSession()
    try:
        # Create test user first if it doesn't exist
        test_user_id = "user_id"
        test_user = session.query(User).filter_by(id=test_user_id).first()
        if not test_user:
            test_user = User(
                id=test_user_id,
                first_name="Test",
                last_name="User",
                email="seed_test_user@example.com",
                password_hash="hashed_password",
            )
            session.add(test_user)
            # Commit user first to ensure it exists before adding categories
            session.flush()

        # Create categories for the test user
        categories = [
            {"id": "cat_alcohol", "user_id": test_user_id, "name": "Alcohol"},
            {"id": "cat_dining", "user_id": test_user_id, "name": "Dining"},
            {"id": "cat_entertainment", "user_id": test_user_id, "name": "Entertainment"},
            {"id": "cat_groceries", "user_id": test_user_id, "name": "Groceries"},
            {"id": "cat_hobbies", "user_id": test_user_id, "name": "Hobbies"},
            {"id": "cat_income", "user_id": test_user_id, "name": "Income"},
            {"id": "cat_investment", "user_id": test_user_id, "name": "Investment"},
            {"id": "cat_medical", "user_id": test_user_id, "name": "Medical"},
            {"id": "cat_rent", "user_id": test_user_id, "name": "Rent"},
            {"id": "cat_shopping", "user_id": test_user_id, "name": "Shopping"},
            {"id": "cat_subscription", "user_id": test_user_id, "name": "Subscription"},
            {"id": "cat_transfer", "user_id": test_user_id, "name": "Transfer"},
            {"id": "cat_transit", "user_id": test_user_id, "name": "Transit"},
            {"id": "cat_travel", "user_id": test_user_id, "name": "Travel"},
            {"id": "cat_food", "user_id": test_user_id, "name": "Food"},
            {"id": "cat_transportation", "user_id": test_user_id, "name": "Transportation"},
        ]
        for cat_data in categories:
            if not session.query(Category).filter_by(user_id=test_user_id, name=cat_data["name"]).first():
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
        # Clean up PostgreSQL tables before each test
        cleanup_test_db()

        # Seed PostgreSQL with base data
        # Skip for phase5 tests as they have their own fixtures
        if "test_phase5" not in request.node.fspath.basename:
            seed_postgresql_base_data()

    def teardown():
        with flask_app.app_context():
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
