import pytest

from dao import line_items_collection, upsert_with_id
from models import LineItem
from resources.line_item import all_line_items


@pytest.fixture
def mock_line_item_data():
    return {
        "id": "line_item_1",
        "date": 1234567890,
        "responsible_party": "John Doe",
        "payment_method": "Cash",
        "description": "Test transaction",
        "amount": 100,
    }


@pytest.fixture
def mock_line_item_with_event():
    return {
        "id": "line_item_2",
        "date": 1234567891,
        "responsible_party": "Jane Smith",
        "payment_method": "Venmo",
        "description": "Test transaction with event",
        "amount": 50,
        "event_id": "event_1",
    }


@pytest.fixture
def line_item_instance():
    return LineItem(
        id="line_item_1",
        date=1234567890,
        responsible_party="John Doe",
        payment_method="Cash",
        description="Test transaction",
        amount=100,
    )


class TestLineItemClass:
    def test_line_item_initialization(self, line_item_instance):
        """Test LineItem class initialization"""
        assert line_item_instance.id == "line_item_1"
        assert line_item_instance.date == 1234567890
        assert line_item_instance.responsible_party == "John Doe"
        assert line_item_instance.payment_method == "Cash"
        assert line_item_instance.description == "Test transaction"
        assert line_item_instance.amount == 100

    def test_line_item_serialize(self, line_item_instance):
        """Test LineItem serialize method"""
        serialized = line_item_instance.model_dump()
        expected = {
            "id": "line_item_1",
            "date": 1234567890,
            "responsible_party": "John Doe",
            "payment_method": "Cash",
            "description": "Test transaction",
            "amount": 100,
        }
        assert serialized == expected

    def test_line_item_to_json(self, line_item_instance):
        """Test LineItem to_json method"""
        json_str = line_item_instance.model_dump_json()
        # Parse back to dict to verify structure
        import json

        parsed = json.loads(json_str)
        assert parsed["id"] == "line_item_1"
        assert parsed["date"] == 1234567890
        assert parsed["responsible_party"] == "John Doe"
        assert parsed["payment_method"] == "Cash"
        assert parsed["description"] == "Test transaction"
        assert parsed["amount"] == 100

    def test_line_item_repr(self, line_item_instance):
        """Test LineItem __repr__ method"""
        repr_str = repr(line_item_instance)
        assert "line_item_1" in repr_str
        assert "John Doe" in repr_str
        assert "Cash" in repr_str
        assert "Test transaction" in repr_str
        assert "100" in repr_str


class TestLineItemAPI:
    def test_get_all_line_items_api(self, test_client, jwt_token, flask_app):
        """Test GET /api/line_items endpoint"""
        # Insert test data
        with flask_app.app_context():
            test_line_items = [
                {
                    "id": "line_item_1",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Cash",
                    "description": "Test transaction 1",
                    "amount": 100,
                },
                {
                    "id": "line_item_2",
                    "date": 1234567891,
                    "responsible_party": "Jane Smith",
                    "payment_method": "Venmo",
                    "description": "Test transaction 2",
                    "amount": 50,
                },
            ]

            for item in test_line_items:
                upsert_with_id(line_items_collection, item, item["id"])

        # Test API call
        response = test_client.get(
            "/api/line_items",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "total" in data
        assert "data" in data
        assert data["total"] == 150  # 100 + 50
        assert len(data["data"]) == 2

    def test_get_all_line_items_with_payment_method_filter(
        self, test_client, jwt_token, flask_app
    ):
        """Test GET /api/line_items with payment_method filter"""
        # Insert test data
        with flask_app.app_context():
            test_line_items = [
                {
                    "id": "line_item_1",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Cash",
                    "description": "Test transaction 1",
                    "amount": 100,
                },
                {
                    "id": "line_item_2",
                    "date": 1234567891,
                    "responsible_party": "Jane Smith",
                    "payment_method": "Venmo",
                    "description": "Test transaction 2",
                    "amount": 50,
                },
            ]

            for item in test_line_items:
                upsert_with_id(line_items_collection, item, item["id"])

        # Test API call with payment_method filter
        response = test_client.get(
            "/api/line_items?payment_method=Cash",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 100
        assert len(data["data"]) == 1
        assert data["data"][0]["payment_method"] == "Cash"

    def test_get_all_line_items_with_review_filter(
        self, test_client, jwt_token, flask_app
    ):
        """Test GET /api/line_items with only_line_items_to_review filter"""
        # Insert test data - one with event_id, one without
        with flask_app.app_context():
            test_line_items = [
                {
                    "id": "line_item_1",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Cash",
                    "description": "Test transaction 1",
                    "amount": 100,
                    # No event_id - should be included in review
                },
                {
                    "id": "line_item_2",
                    "date": 1234567891,
                    "responsible_party": "Jane Smith",
                    "payment_method": "Venmo",
                    "description": "Test transaction 2",
                    "amount": 50,
                    "event_id": "event_1",  # Has event_id - should be excluded
                },
            ]

            for item in test_line_items:
                upsert_with_id(line_items_collection, item, item["id"])

        # Test API call with review filter
        response = test_client.get(
            "/api/line_items?only_line_items_to_review=true",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 100
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "line_item_1"  # Only the one without event_id

    def test_get_line_item_by_id_api_success(self, test_client, flask_app):
        """Test GET /api/line_items/<line_item_id> endpoint - success case"""
        # Insert test data
        with flask_app.app_context():
            test_line_item = {
                "id": "line_item_1",
                "date": 1234567890,
                "responsible_party": "John Doe",
                "payment_method": "Cash",
                "description": "Test transaction",
                "amount": 100,
            }
            upsert_with_id(line_items_collection, test_line_item, test_line_item["id"])

        # Test API call
        response = test_client.get("/api/line_items/line_item_1")

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == "line_item_1"
        assert data["responsible_party"] == "John Doe"
        assert data["payment_method"] == "Cash"
        assert data["description"] == "Test transaction"
        assert data["amount"] == 100

    def test_get_line_item_by_id_api_not_found(self, test_client):
        """Test GET /api/line_items/<line_item_id> endpoint - not found case"""
        response = test_client.get("/api/line_items/nonexistent_id")

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Line item not found"


class TestLineItemFunctions:
    def test_all_line_items_no_filters(self, flask_app):
        """Test all_line_items function with no filters"""
        with flask_app.app_context():
            # Insert test data
            test_line_items = [
                {
                    "id": "line_item_1",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Cash",
                    "description": "Test transaction 1",
                    "amount": 100,
                },
                {
                    "id": "line_item_2",
                    "date": 1234567891,
                    "responsible_party": "Jane Smith",
                    "payment_method": "Venmo",
                    "description": "Test transaction 2",
                    "amount": 50,
                },
            ]

            for item in test_line_items:
                upsert_with_id(line_items_collection, item, item["id"])

            # Test function call
            result = all_line_items()

            assert len(result) == 2
            # Should be sorted by date (reverse=True, so newest first)
            assert result[0]["id"] == "line_item_2"  # Newer date (1234567891)
            assert result[1]["id"] == "line_item_1"  # Older date (1234567890)

    def test_all_line_items_with_payment_method_filter(self, flask_app):
        """Test all_line_items function with payment_method filter"""
        with flask_app.app_context():
            # Insert test data
            test_line_items = [
                {
                    "id": "line_item_1",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Cash",
                    "description": "Test transaction 1",
                    "amount": 100,
                },
                {
                    "id": "line_item_2",
                    "date": 1234567891,
                    "responsible_party": "Jane Smith",
                    "payment_method": "Venmo",
                    "description": "Test transaction 2",
                    "amount": 50,
                },
            ]

            for item in test_line_items:
                upsert_with_id(line_items_collection, item, item["id"])

            # Test function call with payment_method filter
            result = all_line_items(payment_method="Cash")

            assert len(result) == 1
            assert result[0]["payment_method"] == "Cash"
            assert result[0]["id"] == "line_item_1"

    def test_all_line_items_with_review_filter(self, flask_app):
        """Test all_line_items function with only_line_items_to_review filter"""
        with flask_app.app_context():
            # Insert test data - one with event_id, one without
            test_line_items = [
                {
                    "id": "line_item_1",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Cash",
                    "description": "Test transaction 1",
                    "amount": 100,
                    # No event_id - should be included
                },
                {
                    "id": "line_item_2",
                    "date": 1234567891,
                    "responsible_party": "Jane Smith",
                    "payment_method": "Venmo",
                    "description": "Test transaction 2",
                    "amount": 50,
                    "event_id": "event_1",  # Has event_id - should be excluded
                },
            ]

            for item in test_line_items:
                upsert_with_id(line_items_collection, item, item["id"])

            # Test function call with review filter
            result = all_line_items(only_line_items_to_review=True)

            assert len(result) == 1
            assert result[0]["id"] == "line_item_1"  # Only the one without event_id

    def test_all_line_items_with_both_filters(self, flask_app):
        """Test all_line_items function with both payment_method and review filters"""
        with flask_app.app_context():
            # Insert test data
            test_line_items = [
                {
                    "id": "line_item_1",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Cash",
                    "description": "Test transaction 1",
                    "amount": 100,
                    # No event_id - should be included
                },
                {
                    "id": "line_item_2",
                    "date": 1234567891,
                    "responsible_party": "Jane Smith",
                    "payment_method": "Venmo",
                    "description": "Test transaction 2",
                    "amount": 50,
                    # No event_id - should be included
                },
                {
                    "id": "line_item_3",
                    "date": 1234567892,
                    "responsible_party": "Bob Johnson",
                    "payment_method": "Cash",
                    "description": "Test transaction 3",
                    "amount": 75,
                    "event_id": "event_1",  # Has event_id - should be excluded
                },
            ]

            for item in test_line_items:
                upsert_with_id(line_items_collection, item, item["id"])

            # Test function call with both filters
            result = all_line_items(
                payment_method="Cash", only_line_items_to_review=True
            )

            assert len(result) == 1
            assert (
                result[0]["id"] == "line_item_1"
            )  # Only Cash payment method without event_id

    def test_all_line_items_empty_result(self, flask_app):
        """Test all_line_items function with no matching data"""
        with flask_app.app_context():
            # Test function call with no data in database
            result = all_line_items()

            assert len(result) == 0

    def test_all_line_items_payment_method_all(self, flask_app):
        """Test all_line_items function with payment_method='All'"""
        with flask_app.app_context():
            # Insert test data
            test_line_items = [
                {
                    "id": "line_item_1",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Cash",
                    "description": "Test transaction 1",
                    "amount": 100,
                },
                {
                    "id": "line_item_2",
                    "date": 1234567891,
                    "responsible_party": "Jane Smith",
                    "payment_method": "Venmo",
                    "description": "Test transaction 2",
                    "amount": 50,
                },
            ]

            for item in test_line_items:
                upsert_with_id(line_items_collection, item, item["id"])

            # Test function call with payment_method='All'
            result = all_line_items(payment_method="All")

            assert len(result) == 2  # Should return all items, same as no filter
