import os

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from flask_pymongo import PyMongo
from pymongo.errors import ServerSelectionTimeoutError

from constants import JWT_SECRET_KEY
from dao import (
    cash_raw_data_collection,
    events_collection,
    line_items_collection,
    test_collection,
    users_collection,
)
from resources.auth import auth_blueprint
from resources.cash import cash_blueprint
from resources.event import events_blueprint
from resources.line_item import line_items_blueprint

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

    # Use a separate test database
    app.config["MONGO_URI"] = TEST_MONGO_URI
    app.config["MONGO_DB_NAME"] = TEST_DB_NAME

    with app.app_context():
        app.config["MONGO"] = PyMongo(app)
        jwt = JWTManager(app)
        app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY

        # Add user lookup loader for JWT
        @jwt.user_lookup_loader
        def user_lookup_callback(jwt_header, jwt_payload):
            return {"email": "test@example.com", "id": "user_id"}

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
        try:
            # Get the test database
            test_db = flask_app.config["MONGO"].cx[flask_app.config["MONGO_DB_NAME"]]

            # Clean up collections before each test
            test_db.drop_collection(test_collection)
            test_db.drop_collection(cash_raw_data_collection)
            test_db.drop_collection(line_items_collection)
            test_db.drop_collection(events_collection)
            test_db.drop_collection(users_collection)
        except ServerSelectionTimeoutError:
            # This error happens on Github Actions
            pass

    def teardown():
        with flask_app.app_context():
            try:
                # Get the test database
                test_db = flask_app.config["MONGO"].cx[
                    flask_app.config["MONGO_DB_NAME"]
                ]

                # Clean up collections after each test
                test_db.drop_collection(test_collection)
                test_db.drop_collection(cash_raw_data_collection)
                test_db.drop_collection(line_items_collection)
                test_db.drop_collection(events_collection)
                test_db.drop_collection(users_collection)
            except ServerSelectionTimeoutError:
                # This error happens on Github Actions
                pass

    request.addfinalizer(teardown)
