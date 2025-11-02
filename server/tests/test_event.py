import pytest
from datetime import UTC, datetime

from dao import events_collection, line_items_collection, upsert_with_id
from models.sql_models import (
    Category,
    Event,
    EventLineItem,
    EventTag,
    LineItem,
    PaymentMethod,
    Tag,
    Transaction,
)
from utils.id_generator import generate_id


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
def mock_line_item_data_2():
    return {
        "id": "line_item_2",
        "date": 1234567891,
        "responsible_party": "Jane Smith",
        "payment_method": "Venmo",
        "description": "Test transaction 2",
        "amount": 50,
    }


@pytest.fixture
def mock_event_data():
    return {
        "id": "event1",
        "date": 1234567890,
        "description": "Test Event",
        "amount": 150,
        "line_items": ["line_item_1", "line_item_2"],
        "tags": ["test", "event"],
        "is_duplicate_transaction": False,
    }


class TestEventAPI:
    def test_get_all_events_api(self, test_client, jwt_token, flask_app):
        """Test GET /api/events endpoint"""
        # Insert test data
        with flask_app.app_context():
            test_events = [
                {
                    "id": "event1",
                    "date": 1234567890,
                    "description": "Test Event 1",
                    "amount": 100,
                    "line_items": ["line_item_1"],
                    "tags": ["test"],
                },
                {
                    "id": "event2",
                    "date": 1234567891,
                    "description": "Test Event 2",
                    "amount": 50,
                    "line_items": ["line_item_2"],
                    "tags": ["event"],
                },
            ]

            for event in test_events:
                upsert_with_id(events_collection, event, event["id"])

        # Test API call
        response = test_client.get(
            "/api/events",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "total" in data
        assert "data" in data
        assert data["total"] == 150  # 100 + 50
        assert len(data["data"]) == 2

    def test_get_all_events_with_time_filter(self, test_client, jwt_token, flask_app):
        """Test GET /api/events with time filters"""
        # Insert test data
        with flask_app.app_context():
            test_events = [
                {
                    "id": "event1",
                    "date": 1234567890,
                    "description": "Test Event 1",
                    "amount": 100,
                    "line_items": ["line_item_1"],
                    "tags": ["test"],
                },
                {
                    "id": "event2",
                    "date": 1234567891,
                    "description": "Test Event 2",
                    "amount": 50,
                    "line_items": ["line_item_2"],
                    "tags": ["event"],
                },
            ]

            for event in test_events:
                upsert_with_id(events_collection, event, event["id"])

        # Test API call with time filter
        response = test_client.get(
            "/api/events?start_time=1234567890&end_time=1234567890",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 100  # Only the first event
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "event1"

    def test_get_event_by_id_api_success(self, test_client, jwt_token, flask_app):
        """Test GET /api/events/<event_id> endpoint - success case"""
        # Insert test data
        with flask_app.app_context():
            test_event = {
                "id": "event1",
                "date": 1234567890,
                "description": "Test Event",
                "amount": 100,
                "line_items": ["line_item_1"],
                "tags": ["test"],
            }
            upsert_with_id(events_collection, test_event, test_event["id"])

        # Test API call
        response = test_client.get(
            "/api/events/event1",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == "event1"
        assert data["description"] == "Test Event"
        assert data["amount"] == 100

    def test_get_event_by_id_api_not_found(self, test_client, jwt_token):
        """Test GET /api/events/<event_id> endpoint - not found case"""
        response = test_client.get(
            "/api/events/nonexistent_id",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Event not found"

    def test_create_event_api_success(self, test_client, jwt_token, flask_app):
        """Test POST /api/events endpoint - success case"""
        # Insert test line items first
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
        new_event_data = {
            "description": "Test Event",
            "date": "2023-01-01",
            "line_items": ["line_item_1", "line_item_2"],
            "tags": ["test", "event"],
            "is_duplicate_transaction": False,
        }

        response = test_client.post(
            "/api/events",
            json=new_event_data,
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 201
        assert response.get_json() == {
            "_id": "event_1",
            "amount": 150,
            "date": 1672531200.0,
            "description": "Test Event",
            "id": "event_1",
            "is_duplicate_transaction": False,
            "line_items": ["line_item_1", "line_item_2"],
            "tags": ["test", "event"],
        }

        # Verify event was created
        with flask_app.app_context():
            from dao import get_item_by_id

            created_event = get_item_by_id(events_collection, "event_1")
            assert created_event is not None
            assert created_event["description"] == "Test Event"
            assert created_event["amount"] == 150  # 100 + 50
            assert created_event["line_items"] == ["line_item_1", "line_item_2"]

            # Verify line items were updated with event_id
            line_item_1 = get_item_by_id(line_items_collection, "line_item_1")
            line_item_2 = get_item_by_id(line_items_collection, "line_item_2")
            assert line_item_1 is not None
            assert line_item_2 is not None
            assert line_item_1["event_id"] == "event_1"
            assert line_item_2["event_id"] == "event_1"

    def test_create_event_api_no_line_items(self, test_client, jwt_token):
        """Test POST /api/events endpoint - no line items"""
        new_event_data = {
            "description": "Test Event",
            "date": "2023-01-01",
            "line_items": [],
            "tags": ["test"],
            "is_duplicate_transaction": False,
        }

        response = test_client.post(
            "/api/events",
            json=new_event_data,
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 400
        assert (
            response.get_data(as_text=True).strip()
            == '"Failed to Create Event: No Line Items Submitted"'
        )

    def test_create_event_api_duplicate_transaction(
        self, test_client, jwt_token, flask_app
    ):
        """Test POST /api/events endpoint - duplicate transaction"""
        # Insert test line items first
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
            ]

            for item in test_line_items:
                upsert_with_id(line_items_collection, item, item["id"])

        # Test API call with duplicate transaction
        new_event_data = {
            "description": "Test Event",
            "date": "2023-01-01",
            "line_items": ["line_item_1"],
            "tags": ["test"],
            "is_duplicate_transaction": True,
        }

        response = test_client.post(
            "/api/events",
            json=new_event_data,
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 201

        # Verify event was created with correct amount (should be line_item_1 amount only)
        with flask_app.app_context():
            from dao import get_item_by_id

            created_event = get_item_by_id(events_collection, "event_1")
            assert created_event is not None
            assert created_event["amount"] == 100  # Only the first line item amount

    def test_create_event_api_no_date(self, test_client, jwt_token, flask_app):
        """Test POST /api/events endpoint - no date provided"""
        # Insert test line items first
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
            ]

            for item in test_line_items:
                upsert_with_id(line_items_collection, item, item["id"])

        # Test API call without date
        new_event_data = {
            "description": "Test Event",
            "date": None,
            "line_items": ["line_item_1"],
            "tags": ["test"],
            "is_duplicate_transaction": False,
        }

        response = test_client.post(
            "/api/events",
            json=new_event_data,
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 201

        # Verify event was created with earliest line item date
        with flask_app.app_context():
            from dao import get_item_by_id

            created_event = get_item_by_id(events_collection, "event_1")
            assert created_event is not None
            assert (
                created_event["date"] == 1234567890
            )  # Should use earliest line item date

    def test_delete_event_api_success(self, test_client, jwt_token, flask_app):
        """Test DELETE /api/events/<event_id> endpoint - success case"""
        # Insert test data
        with flask_app.app_context():
            test_event = {
                "id": "event_1",
                "date": 1234567890,
                "description": "Test Event",
                "amount": 100,
                "line_items": ["line_item_1"],
                "tags": ["test"],
            }
            upsert_with_id(events_collection, test_event, test_event["id"])

            # Insert line item with event_id
            test_line_item = {
                "id": "line_item_1",
                "date": 1234567890,
                "responsible_party": "John Doe",
                "payment_method": "Cash",
                "description": "Test transaction",
                "amount": 100,
                "event_id": "event_1",
            }
            upsert_with_id(line_items_collection, test_line_item, test_line_item["id"])

        # Test API call
        response = test_client.delete(
            "/api/events/event_1",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        assert response.get_data(as_text=True).strip() == '"Deleted Event"'

        # Verify event was deleted
        with flask_app.app_context():
            from dao import get_item_by_id

            deleted_event = get_item_by_id(events_collection, "event_1")
            assert deleted_event is None

            # Verify line item event_id was removed
            line_item = get_item_by_id(line_items_collection, "line_item_1")
            assert line_item is not None
            assert "event_id" not in line_item

    def test_delete_event_api_not_found(self, test_client, jwt_token):
        """Test DELETE /api/events/<event_id> endpoint - not found case"""
        response = test_client.delete(
            "/api/events/nonexistent_id",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Event not found"

    def test_get_line_items_for_event_api_success(
        self, test_client, jwt_token, flask_app
    ):
        """Test GET /api/events/<event_id>/line_items_for_event endpoint - success case"""
        # Insert test data
        with flask_app.app_context():
            test_event = {
                "id": "event1",
                "date": 1234567890,
                "description": "Test Event",
                "amount": 150,
                "line_items": ["line_item_1", "line_item_2"],
                "tags": ["test"],
            }
            upsert_with_id(events_collection, test_event, test_event["id"])

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
            "/api/events/event1/line_items_for_event",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == "line_item_1"
        assert data["data"][1]["id"] == "line_item_2"

    def test_get_line_items_for_event_api_not_found(self, test_client, jwt_token):
        """Test GET /api/events/<event_id>/line_items_for_event endpoint - not found case"""
        response = test_client.get(
            "/api/events/nonexistent_id/line_items_for_event",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Event not found"

    def test_get_line_items_for_event_api_missing_line_item(
        self, test_client, jwt_token, flask_app
    ):
        """Test GET /api/events/<event_id>/line_items_for_event endpoint - missing line item"""
        # Insert test data with one missing line item
        with flask_app.app_context():
            test_event = {
                "id": "event1",
                "date": 1234567890,
                "description": "Test Event",
                "amount": 100,
                "line_items": ["line_item_1", "nonexistent_line_item"],
                "tags": ["test"],
            }
            upsert_with_id(events_collection, test_event, test_event["id"])

            # Only insert one line item
            test_line_item = {
                "id": "line_item_1",
                "date": 1234567890,
                "responsible_party": "John Doe",
                "payment_method": "Cash",
                "description": "Test transaction 1",
                "amount": 100,
            }
            upsert_with_id(line_items_collection, test_line_item, test_line_item["id"])

        # Test API call
        response = test_client.get(
            "/api/events/event1/line_items_for_event",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) == 1  # Only the existing line item
        assert data["data"][0]["id"] == "line_item_1"

    def test_remove_event_from_line_item_different_id_types(self, flask_app):
        """Test remove_event_from_line_item function with different ID types"""
        with flask_app.app_context():
            from bson import ObjectId

            from dao import get_item_by_id, remove_event_from_line_item

            # Test with string ID
            test_line_item_str = {
                "id": "line_item_str",
                "date": 1234567890,
                "responsible_party": "John Doe",
                "payment_method": "Cash",
                "description": "Test transaction",
                "amount": 100,
                "event_id": "event_1",
            }
            upsert_with_id(
                line_items_collection, test_line_item_str, test_line_item_str["id"]
            )

            # Test with integer ID
            test_line_item_int = {
                "id": 12345,
                "date": 1234567891,
                "responsible_party": "Jane Smith",
                "payment_method": "Venmo",
                "description": "Test transaction 2",
                "amount": 50,
                "event_id": "event_2",
            }
            upsert_with_id(
                line_items_collection, test_line_item_int, test_line_item_int["id"]
            )

            # Test with ObjectId
            test_line_item_objectid = {
                "id": ObjectId(),
                "date": 1234567892,
                "responsible_party": "Bob Johnson",
                "payment_method": "Stripe",
                "description": "Test transaction 3",
                "amount": 75,
                "event_id": "event_3",
            }
            upsert_with_id(
                line_items_collection,
                test_line_item_objectid,
                test_line_item_objectid["id"],
            )

            # Verify all line items have event_id
            line_item_str = get_item_by_id(line_items_collection, "line_item_str")
            line_item_int = get_item_by_id(line_items_collection, 12345)
            line_item_objectid = get_item_by_id(
                line_items_collection, test_line_item_objectid["id"]
            )
            assert line_item_str is not None
            assert line_item_int is not None
            assert line_item_objectid is not None
            assert line_item_str["event_id"] == "event_1"
            assert line_item_int["event_id"] == "event_2"
            assert line_item_objectid["event_id"] == "event_3"

            # Test removing event_id with string ID
            remove_event_from_line_item("line_item_str")
            line_item_str_after = get_item_by_id(line_items_collection, "line_item_str")
            assert line_item_str_after is not None
            assert "event_id" not in line_item_str_after

            # Test removing event_id with integer ID
            remove_event_from_line_item(12345)
            line_item_int_after = get_item_by_id(line_items_collection, 12345)
            assert line_item_int_after is not None
            assert "event_id" not in line_item_int_after

            # Test removing event_id with ObjectId
            remove_event_from_line_item(test_line_item_objectid["id"])
            line_item_objectid_after = get_item_by_id(
                line_items_collection, test_line_item_objectid["id"]
            )
            assert line_item_objectid_after is not None
            assert "event_id" not in line_item_objectid_after


class TestEventDualWrite:
    """Test dual-write functionality for events (Phase 4)"""

    @pytest.fixture(autouse=True)
    def setup_postgres_data(self, pg_session):
        """Set up necessary PostgreSQL data for event creation"""
        # Create category
        category = Category(
            id=generate_id("cat"),
            name="Dining",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        pg_session.add(category)

        # Create payment method
        payment_method = PaymentMethod(
            id=generate_id("pm"),
            name="Cash",
            type="cash",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        pg_session.add(payment_method)

        # Create transaction
        transaction = Transaction(
            id=generate_id("txn"),
            source="manual",
            source_id="manual_test",
            source_data={"description": "Test transaction"},
            transaction_date=datetime.fromtimestamp(1234567890, UTC),
            created_at=datetime.now(UTC),
        )
        pg_session.add(transaction)

        # Create line items in PostgreSQL
        line_item_1 = LineItem(
            id="li_test1",
            transaction_id=transaction.id,
            mongo_id="line_item_1",
            date=datetime.fromtimestamp(1234567890, UTC),
            amount=100.00,
            description="Test transaction 1",
            payment_method_id=payment_method.id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        line_item_2 = LineItem(
            id="li_test2",
            transaction_id=transaction.id,
            mongo_id="line_item_2",
            date=datetime.fromtimestamp(1234567891, UTC),
            amount=50.00,
            description="Test transaction 2",
            payment_method_id=payment_method.id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        pg_session.add(line_item_1)
        pg_session.add(line_item_2)

        pg_session.commit()

    def test_create_event_dual_write_success(
        self, test_client, jwt_token, flask_app, pg_session
    ):
        """Test that creating an event writes to both MongoDB and PostgreSQL"""
        # Insert test line items in MongoDB
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
                    "payment_method": "Cash",
                    "description": "Test transaction 2",
                    "amount": 50,
                },
            ]

            for item in test_line_items:
                upsert_with_id(line_items_collection, item, item["id"])

        # Create event via API
        new_event_data = {
            "name": "Test Event",  # Frontend sends 'name'
            "category": "Dining",
            "date": "2023-01-01",
            "line_items": ["line_item_1", "line_item_2"],
            "tags": ["test", "event"],
            "is_duplicate_transaction": False,
        }

        response = test_client.post(
            "/api/events",
            json=new_event_data,
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 201

        # Verify MongoDB write
        with flask_app.app_context():
            from dao import get_item_by_id

            mongo_event = get_item_by_id(events_collection, "event_1")
            assert mongo_event is not None
            assert mongo_event["name"] == "Test Event"
            assert mongo_event["amount"] == 150

        # Verify PostgreSQL write
        pg_event = pg_session.query(Event).filter(Event.mongo_id == "event_1").first()
        assert pg_event is not None
        assert pg_event.description == "Test Event"
        assert pg_event.category.name == "Dining"
        assert pg_event.is_duplicate is False

        # Verify EventLineItem junctions created
        pg_junctions = (
            pg_session.query(EventLineItem)
            .filter(EventLineItem.event_id == pg_event.id)
            .all()
        )
        assert len(pg_junctions) == 2

        # Verify EventTag junctions created
        pg_event_tags = (
            pg_session.query(EventTag).filter(EventTag.event_id == pg_event.id).all()
        )
        assert len(pg_event_tags) == 2

        # Verify tags were created
        pg_tags = pg_session.query(Tag).all()
        tag_names = {tag.name for tag in pg_tags}
        assert "test" in tag_names
        assert "event" in tag_names

    def test_create_event_existing_tags(
        self, test_client, jwt_token, flask_app, pg_session
    ):
        """Test that creating an event with existing tags doesn't duplicate them"""
        # Pre-create tags in PostgreSQL
        existing_tag = Tag(
            id=generate_id("tag"),
            name="existing_tag",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        pg_session.add(existing_tag)
        pg_session.commit()

        initial_tag_count = pg_session.query(Tag).count()

        # Insert test line items in MongoDB
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

        # Create event with existing tag
        new_event_data = {
            "name": "Test Event",
            "category": "Dining",
            "date": "2023-01-01",
            "line_items": ["line_item_1"],
            "tags": ["existing_tag", "new_tag"],
            "is_duplicate_transaction": False,
        }

        response = test_client.post(
            "/api/events",
            json=new_event_data,
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 201

        # Verify only new tag was created
        final_tag_count = pg_session.query(Tag).count()
        assert final_tag_count == initial_tag_count + 1  # Only "new_tag" added

    def test_delete_event_dual_write_success(
        self, test_client, jwt_token, flask_app, pg_session
    ):
        """Test that deleting an event removes from both MongoDB and PostgreSQL"""
        # Create event in MongoDB
        with flask_app.app_context():
            test_event = {
                "id": "event_1",
                "date": 1234567890,
                "description": "Test Event",
                "category": "Dining",
                "amount": 100,
                "line_items": ["line_item_1"],
                "tags": ["test"],
                "is_duplicate_transaction": False,
            }
            upsert_with_id(events_collection, test_event, test_event["id"])

            # Create line item with event_id
            test_line_item = {
                "id": "line_item_1",
                "date": 1234567890,
                "responsible_party": "John Doe",
                "payment_method": "Cash",
                "description": "Test transaction",
                "amount": 100,
                "event_id": "event_1",
            }
            upsert_with_id(line_items_collection, test_line_item, test_line_item["id"])

        # Create event in PostgreSQL
        category = pg_session.query(Category).filter(Category.name == "Dining").first()
        tag = Tag(
            id=generate_id("tag"),
            name="test",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        pg_session.add(tag)

        pg_event = Event(
            id=generate_id("event"),
            mongo_id="event_1",
            date=datetime.fromtimestamp(1234567890, UTC),
            description="Test Event",
            category_id=category.id,
            is_duplicate=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        pg_session.add(pg_event)

        # Create junction records
        event_line_item = EventLineItem(
            id=generate_id("eli"),
            event_id=pg_event.id,
            line_item_id="li_test1",
            created_at=datetime.now(UTC),
        )
        pg_session.add(event_line_item)

        event_tag = EventTag(
            id=generate_id("etag"),
            event_id=pg_event.id,
            tag_id=tag.id,
            created_at=datetime.now(UTC),
        )
        pg_session.add(event_tag)
        pg_session.commit()

        # Capture event ID before deletion for cascade verification
        pg_event_id = pg_event.id

        # Verify setup
        assert (
            pg_session.query(Event).filter(Event.mongo_id == "event_1").first()
            is not None
        )
        assert (
            pg_session.query(EventLineItem)
            .filter(EventLineItem.event_id == pg_event_id)
            .count()
            == 1
        )
        assert (
            pg_session.query(EventTag).filter(EventTag.event_id == pg_event_id).count()
            == 1
        )

        # Delete event via API
        response = test_client.delete(
            "/api/events/event_1",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200

        # Verify MongoDB deletion
        with flask_app.app_context():
            from dao import get_item_by_id

            deleted_event = get_item_by_id(events_collection, "event_1")
            assert deleted_event is None

            # Verify line item event_id removed
            line_item = get_item_by_id(line_items_collection, "line_item_1")
            assert line_item is not None
            assert "event_id" not in line_item

        # Verify PostgreSQL deletion (create new session to avoid stale references)
        pg_session.close()
        from models.database import SessionLocal

        fresh_session = SessionLocal()

        deleted_pg_event = (
            fresh_session.query(Event).filter(Event.mongo_id == "event_1").first()
        )
        assert deleted_pg_event is None

        # Verify cascade deletion of junctions
        remaining_junctions = (
            fresh_session.query(EventLineItem)
            .filter(EventLineItem.event_id == pg_event_id)
            .count()
        )
        assert remaining_junctions == 0

        remaining_event_tags = (
            fresh_session.query(EventTag)
            .filter(EventTag.event_id == pg_event_id)
            .count()
        )
        assert remaining_event_tags == 0

        fresh_session.close()

    def test_delete_event_id_coexistence(
        self, test_client, jwt_token, flask_app, pg_session
    ):
        """Test that delete works with both MongoDB and PostgreSQL ID formats"""
        # Create event in MongoDB
        with flask_app.app_context():
            test_event = {
                "id": "event_1",
                "date": 1234567890,
                "description": "Test Event",
                "category": "Dining",
                "amount": 100,
                "line_items": ["line_item_1"],
                "tags": [],
                "is_duplicate_transaction": False,
            }
            upsert_with_id(events_collection, test_event, test_event["id"])

        # Create event in PostgreSQL with event_ prefix
        category = pg_session.query(Category).filter(Category.name == "Dining").first()
        pg_event = Event(
            id="event_01JA8QM9TN",  # PostgreSQL ID with event_ prefix
            mongo_id="event_1",
            date=datetime.fromtimestamp(1234567890, UTC),
            description="Test Event",
            category_id=category.id,
            is_duplicate=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        pg_session.add(pg_event)
        pg_session.commit()

        # Delete using MongoDB ID format
        response = test_client.delete(
            "/api/events/event_1",  # MongoDB ID
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200

        # Verify both deleted
        with flask_app.app_context():
            from dao import get_item_by_id

            assert get_item_by_id(events_collection, "event_1") is None

        pg_session.expire_all()
        assert (
            pg_session.query(Event).filter(Event.mongo_id == "event_1").first() is None
        )
