import pytest
from constants import JWT_SECRET_KEY, MONGODB_DB_NAME, MONGODB_HOST
from dao import cash_raw_data_collection, line_items_collection
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from flask_pymongo import PyMongo
from pymongo.errors import ServerSelectionTimeoutError
from resources.cash import cash_blueprint


@pytest.fixture
def flask_app():
    app = Flask(__name__)
    app.debug = True
    app.register_blueprint(cash_blueprint)
    with app.app_context():
        app.config["MONGO_URI"] = f"mongodb://{MONGODB_HOST}:27017/{MONGODB_DB_NAME}"
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
            flask_app.config["MONGO"].db.drop_collection(cash_raw_data_collection)
            flask_app.config["MONGO"].db.drop_collection(line_items_collection)
        except ServerSelectionTimeoutError:
            # This error happens on Github Actions
            pass

    def teardown():
        with flask_app.app_context():
            try:
                flask_app.config["MONGO"].db.drop_collection(cash_raw_data_collection)
                flask_app.config["MONGO"].db.drop_collection(line_items_collection)
            except ServerSelectionTimeoutError:
                # This error happens on Github Actions
                pass

    request.addfinalizer(teardown)
