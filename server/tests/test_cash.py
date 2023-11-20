import unittest

from constants import JWT_COOKIE_DOMAIN, JWT_SECRET_KEY, MONGODB_HOST
from dao import (
    cash_raw_data_collection,
    get_all_data,
    line_items_collection,
    upsert_with_id,
)
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from flask_pymongo import PyMongo
from helpers import html_date_to_posix
from resources.cash import cash_blueprint, cash_to_line_items
from resources.line_item import LineItem

MONGODB_DB_NAME = "test_db"


class CashBlueprintTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.debug = True
        self.app.register_blueprint(cash_blueprint)
        self.client = self.app.test_client()
        with self.app.app_context():
            self.app.config[
                "MONGO_URI"
            ] = f"mongodb://{MONGODB_HOST}:27017/{MONGODB_DB_NAME}"
            self.app.config["MONGO"] = PyMongo(self.app)
            jwt = JWTManager(self.app)
            # JWT Config Links
            # - https://flask-jwt-extended.readthedocs.io/en/stable/options.html
            # - https://flask-jwt-extended.readthedocs.io/en/3.0.0_release/tokens_in_cookies/
            self.app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
            self.app.config["JWT_COOKIE_DOMAIN"] = JWT_COOKIE_DOMAIN
            self.app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
            self.app.config["JWT_ACCESS_COOKIE_PATH"] = "/api/"
            self.app.config["JWT_COOKIE_SAMESITE"] = "Lax"
            self.app.config["JWT_COOKIE_CSRF_PROTECT"] = False
            # Generate a valid JWT token for testing
            self.test_token = create_access_token(identity="64cdf883a2a08295f6371fda")
            self.client.set_cookie("localhost", "access_token_cookie", self.test_token)

    def tearDown(self):
        # Clean up resources
        with self.app.app_context():
            self.app.config["MONGO"].db.drop_collection(cash_raw_data_collection)
            self.app.config["MONGO"].db.drop_collection(line_items_collection)

    def test_create_cash_transaction_api(self):
        # Define a mock request with JSON data
        mock_request_data = {
            "date": "2023-09-15",
            "person": "John Doe",
            "description": "Test transaction",
            "amount": 100,
        }

        # Send a POST request to the API
        response = self.client.post(
            "/api/cash_transaction",
            json=mock_request_data,
            headers={"Authorization": "Bearer " + self.test_token},
        )

        # Ensure that the status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Ensure that the JSON response is as expected
        expected_response = "Created Cash Transaction"
        self.assertEqual(response.get_json(), expected_response)

        # Ensure that the DB state is as expected
        with self.app.app_context():
            cash_db = get_all_data(cash_raw_data_collection)
            self.assertEqual(len(cash_db), 1)
            item_in_db = cash_db[0]
            self.assertEqual(
                item_in_db["date"], html_date_to_posix(mock_request_data["date"])
            )
            self.assertEqual(item_in_db["person"], mock_request_data["person"])
            self.assertEqual(
                item_in_db["description"], mock_request_data["description"]
            )
            self.assertEqual(item_in_db["amount"], mock_request_data["amount"])

    def test_cash_to_line_items(self):
        # Set up mock data for cash_raw_data
        mock_cash_raw_data = {
            "id": 1,
            "date": 1234567890,
            "person": "John Doe",
            "description": "Test transaction",
            "amount": 100,
        }

        expected_line_item = LineItem(
            "line_item_1",
            1234567890,
            "John Doe",
            "Cash",
            "Test transaction",
            100,
        )

        with self.app.app_context():
            upsert_with_id(
                cash_raw_data_collection, mock_cash_raw_data, mock_cash_raw_data["id"]
            )

            # Call the cash_to_line_items function
            cash_to_line_items()

            # Ensure that the DB state is as expected
            line_items_db = get_all_data(line_items_collection)
            self.assertEqual(len(line_items_db), 1)
            item_in_db = line_items_db[0]
            self.assertEqual(item_in_db["id"], expected_line_item.id)
            self.assertEqual(item_in_db["date"], expected_line_item.date)
            self.assertEqual(
                item_in_db["responsible_party"], expected_line_item.responsible_party
            )
            self.assertEqual(item_in_db["description"], expected_line_item.description)
            self.assertEqual(item_in_db["amount"], expected_line_item.amount)

        # Ensure that upsert was called with the correct LineItem objects


if __name__ == "__main__":
    unittest.main()
