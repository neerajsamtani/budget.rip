import pytest

from dao import get_all_data, get_collection, insert, test_collection


@pytest.fixture
def mock_collection(flask_app):
    with flask_app.app_context():
        return get_collection(test_collection)


def test_get_all_data(flask_app, mock_collection):
    with flask_app.app_context():
        # Insert documents into the collection
        document_a = {"name": "John", "age": 30}
        document_b = {"name": "John", "age": 30}
        mock_collection.insert_one(document_a)
        mock_collection.insert_one(document_b)

        # Query all documents from the collection
        response = get_all_data(test_collection)

        assert len(response) == 2
        assert response[0]["name"] == document_a["name"]
        assert response[0]["age"] == document_a["age"]
        assert response[1]["name"] == document_b["name"]
        assert response[1]["age"] == document_b["age"]


def test_get_all_data_when_no_data_returns_empty_list(flask_app):
    with flask_app.app_context():
        # Query all documents from the empty collection
        response = get_all_data(test_collection)

        assert len(response) == 0


def test_insert(flask_app, mock_collection):
    with flask_app.app_context():
        # Insert a document into the collection
        document = {"name": "John", "age": 30}
        insert(test_collection, document)

        # Query the inserted document
        retrieved_document = mock_collection.find_one({"name": "John"})

        # Assert that the retrieved document matches the inserted document
        assert document["name"] == retrieved_document["name"]
        assert document["age"] == retrieved_document["age"]
