import unittest

from constants import MONGODB_HOST
from dao import get_all_data, insert, get_collection
from flask import Flask
from flask_pymongo import PyMongo
from pymongo.errors import ServerSelectionTimeoutError

MONGODB_DB_NAME = "test_db"
TEST_COLLECTION = "test_collection"


class TestDao(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.debug = True
        self.client = self.app.test_client()
        with self.app.app_context():
            self.app.config[
                "MONGO_URI"
            ] = f"mongodb://{MONGODB_HOST}:27017/{MONGODB_DB_NAME}"
            self.app.config["MONGO"] = PyMongo(self.app)

    def tearDown(self):
        # Clean up resources
        with self.app.app_context():
            try:
                self.app.config["MONGO"].db.drop_collection(TEST_COLLECTION)
            except ServerSelectionTimeoutError:
                # This error happens on Github Actions
                pass

    def test_get_all_data(self):
        with self.app.app_context():
            cur_collection = get_collection(TEST_COLLECTION)
            # Insert documents into the collection
            document_a = {"name": "John", "age": 30}
            document_b = {"name": "John", "age": 30}
            cur_collection.insert_one(document_a)
            cur_collection.insert_one(document_b)
            response = get_all_data(TEST_COLLECTION)
            self.assertEqual(len(response), 2)
            self.assertEqual(response[0]["name"], document_a["name"])
            self.assertEqual(response[0]["age"], document_a["age"])
            self.assertEqual(response[1]["name"], document_b["name"])
            self.assertEqual(response[1]["age"], document_b["age"])

    def test_get_all_data_when_no_data_returns_empty_list(self):
        with self.app.app_context():
            # Insert documents into the collection
            response = get_all_data(TEST_COLLECTION)
            self.assertEqual(len(response), 0)

    # Your test methods go here
    def test_insert(self):
        with self.app.app_context():
            # Insert a document into the collection
            document = {"name": "John", "age": 30}
            insert(TEST_COLLECTION, document)

            # Query the inserted document
            cur_collection = get_collection(TEST_COLLECTION)
            retrieved_document = cur_collection.find_one({"name": "John"})

            # Assert that the retrieved document matches the inserted document
            self.assertEqual(document["name"], retrieved_document["name"])
            self.assertEqual(document["age"], retrieved_document["age"])
