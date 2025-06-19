import os

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from flask_pymongo import PyMongo
from pymongo.errors import ServerSelectionTimeoutError

from constants import JWT_SECRET_KEY
from dao import cash_raw_data_collection, line_items_collection, test_collection
from resources.cash import cash_blueprint

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
    app.register_blueprint(cash_blueprint)

    # Use a separate test database
    app.config["MONGO_URI"] = TEST_MONGO_URI
    app.config["MONGO_DB_NAME"] = TEST_DB_NAME

    with app.app_context():
        app.config["MONGO"] = PyMongo(app)
        JWTManager(app)
        app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
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
            except ServerSelectionTimeoutError:
                # This error happens on Github Actions
                pass

    request.addfinalizer(teardown)
