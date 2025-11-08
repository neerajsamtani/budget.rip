from datetime import UTC, datetime

import pytest

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
        "name": "Test Event",
        "amount": 150,
        "line_items": ["line_item_1", "line_item_2"],
        "tags": ["test", "event"],
        "is_duplicate_transaction": False,
    }


class TestEventAPI:
    def test_get_all_events_api(
        self,
        test_client,
        jwt_token,
        flask_app,
        create_line_item_via_cash,
        create_event_via_api,
    ):
        """Test GET /api/events endpoint"""
        # Create test line items via API
        create_line_item_via_cash(
            date="2009-02-13", person="Person1", description="Transaction 1", amount=100
        )
        create_line_item_via_cash(
            date="2009-02-14", person="Person2", description="Transaction 2", amount=50
        )

        # Get created line item IDs
        with flask_app.app_context():
            from dao import get_all_data

            all_line_items = get_all_data(line_items_collection)
            line_item_ids = [item["id"] for item in all_line_items]
            assert len(line_item_ids) == 2

        # Create events via API
        create_event_via_api(
            {
                "name": "Test Event 1",
                "category": "Dining",
                "date": "2009-02-13",
                "line_items": [line_item_ids[0]],
                "tags": ["test"],
                "is_duplicate_transaction": False,
            }
        )
        create_event_via_api(
            {
                "name": "Test Event 2",
                "category": "Dining",
                "date": "2009-02-14",
                "line_items": [line_item_ids[1]],
                "tags": ["event"],
                "is_duplicate_transaction": False,
            }
        )

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

    def test_get_all_events_with_time_filter(
        self,
        test_client,
        jwt_token,
        flask_app,
        create_line_item_via_cash,
        create_event_via_api,
    ):
        """Test GET /api/events with time filters"""
        # Create test line items via API
        create_line_item_via_cash(
            date="2009-02-13", person="Person1", description="Transaction 1", amount=100
        )
        create_line_item_via_cash(
            date="2009-02-14", person="Person2", description="Transaction 2", amount=50
        )

        # Get created line item IDs and dates (sort by date to ensure consistent ordering)
        with flask_app.app_context():
            from dao import get_all_data

            all_line_items = get_all_data(line_items_collection)
            all_line_items_sorted = sorted(all_line_items, key=lambda x: x["date"])
            assert len(all_line_items_sorted) == 2
            line_item_feb13 = all_line_items_sorted[0]  # 2009-02-13, amount=100
            line_item_feb14 = all_line_items_sorted[1]  # 2009-02-14, amount=50

        # Create events via API
        event1_response = create_event_via_api(
            {
                "name": "Test Event 1",
                "category": "Dining",
                "date": "2009-02-13",
                "line_items": [line_item_feb13["id"]],
                "tags": ["test"],
                "is_duplicate_transaction": False,
            }
        )
        create_event_via_api(
            {
                "name": "Test Event 2",
                "category": "Dining",
                "date": "2009-02-14",
                "line_items": [line_item_feb14["id"]],
                "tags": ["event"],
                "is_duplicate_transaction": False,
            }
        )
        event1_id = event1_response["id"]
        event_1_date = line_item_feb13["date"]

        # Test API call with time filter (filter to only first event's date)
        response = test_client.get(
            f"/api/events?start_time={int(event_1_date)}&end_time={int(event_1_date)}",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 100  # Only the first event
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == event1_id

    def test_get_event_by_id_api_success(
        self,
        test_client,
        jwt_token,
        flask_app,
        create_line_item_via_cash,
        create_event_via_api,
    ):
        """Test GET /api/events/<event_id> endpoint - success case"""
        # Create test line item via API
        create_line_item_via_cash(
            date="2009-02-13", person="Person1", description="Transaction 1", amount=100
        )

        # Get created line item ID
        with flask_app.app_context():
            from dao import get_all_data

            all_line_items = get_all_data(line_items_collection)
            line_item_ids = [item["id"] for item in all_line_items]
            assert len(line_item_ids) == 1

        # Create event via API
        event_response = create_event_via_api(
            {
                "name": "Test Event",
                "category": "Dining",
                "date": "2009-02-13",
                "line_items": line_item_ids,
                "tags": ["test"],
                "is_duplicate_transaction": False,
            }
        )
        event_id = event_response["id"]

        # Test API call
        response = test_client.get(
            f"/api/events/{event_id}",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == event_id
        assert data["name"] == "Test Event"
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

    def test_create_event_api_success(
        self, test_client, jwt_token, flask_app, create_line_item_via_cash
    ):
        """Test POST /api/events endpoint - success case"""
        # Create test line items via API
        create_line_item_via_cash(
            date="2009-02-13",
            person="John Doe",
            description="Test transaction 1",
            amount=100,
        )
        create_line_item_via_cash(
            date="2009-02-14",
            person="Jane Smith",
            description="Test transaction 2",
            amount=50,
        )

        # Get created line item IDs
        with flask_app.app_context():
            from dao import get_all_data

            all_line_items = get_all_data(line_items_collection)
            line_item_ids = [item["id"] for item in all_line_items]
            assert len(line_item_ids) == 2

        # Test API call with dynamic line item IDs
        new_event_data = {
            "name": "Test Event",
            "category": "Dining",
            "date": "2023-01-01",
            "line_items": line_item_ids,
            "tags": ["test", "event"],
            "is_duplicate_transaction": False,
        }

        response = test_client.post(
            "/api/events",
            json=new_event_data,
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 201
        response_data = response.get_json()
        assert response_data["amount"] == 150
        assert response_data["name"] == "Test Event"
        assert response_data["is_duplicate_transaction"] is False
        assert set(response_data["line_items"]) == set(line_item_ids)
        assert set(response_data["tags"]) == {"test", "event"}
        created_event_id = response_data["id"]

        # Verify event was created
        with flask_app.app_context():
            from dao import get_item_by_id

            created_event = get_item_by_id(events_collection, created_event_id)
            assert created_event is not None
            assert created_event["name"] == "Test Event"
            assert created_event["amount"] == 150  # 100 + 50
            assert set(created_event["line_items"]) == set(line_item_ids)

            # Verify line items were updated with event_id
            for li_id in line_item_ids:
                line_item = get_item_by_id(line_items_collection, li_id)
                assert line_item is not None
                assert line_item["event_id"] == created_event_id

    def test_create_event_api_no_line_items(self, test_client, jwt_token):
        """Test POST /api/events endpoint - no line items"""
        new_event_data = {
            "name": "Test Event",
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
        self, test_client, jwt_token, flask_app, create_line_item_via_cash
    ):
        """Test POST /api/events endpoint - duplicate transaction"""
        # Create test line item via API
        create_line_item_via_cash(
            date="2009-02-13",
            person="John Doe",
            description="Test transaction 1",
            amount=100,
        )

        # Get created line item ID
        with flask_app.app_context():
            from dao import get_all_data

            all_line_items = get_all_data(line_items_collection)
            line_item_ids = [item["id"] for item in all_line_items]
            assert len(line_item_ids) == 1

        # Test API call with duplicate transaction
        new_event_data = {
            "name": "Test Event",
            "category": "Dining",
            "date": "2023-01-01",
            "line_items": line_item_ids,
            "tags": ["test"],
            "is_duplicate_transaction": True,
        }

        response = test_client.post(
            "/api/events",
            json=new_event_data,
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 201
        response_data = response.get_json()
        created_event_id = response_data["id"]

        # Verify event was created with correct amount (should be line_item_1 amount only)
        with flask_app.app_context():
            from dao import get_item_by_id

            created_event = get_item_by_id(events_collection, created_event_id)
            assert created_event is not None
            assert created_event["amount"] == 100  # Only the first line item amount

    def test_create_event_api_no_date(
        self, test_client, jwt_token, flask_app, create_line_item_via_cash
    ):
        """Test POST /api/events endpoint - no date provided"""
        # Create test line item via API
        create_line_item_via_cash(
            date="2009-02-13",
            person="John Doe",
            description="Test transaction 1",
            amount=100,
        )

        # Get created line item ID
        with flask_app.app_context():
            from dao import get_all_data

            all_line_items = get_all_data(line_items_collection)
            line_item_ids = [item["id"] for item in all_line_items]
            assert len(line_item_ids) == 1

        # Test API call without date
        new_event_data = {
            "name": "Test Event",
            "category": "Dining",
            "date": None,
            "line_items": line_item_ids,
            "tags": ["test"],
            "is_duplicate_transaction": False,
        }

        response = test_client.post(
            "/api/events",
            json=new_event_data,
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 201
        response_data = response.get_json()
        created_event_id = response_data["id"]

        # Verify event was created with earliest line item date
        with flask_app.app_context():
            from dao import get_item_by_id

            created_event = get_item_by_id(events_collection, created_event_id)
            assert created_event is not None
            assert (
                created_event["date"] == all_line_items[0]["date"]
            )  # Should use earliest line item date

    def test_delete_event_api_success(
        self,
        test_client,
        jwt_token,
        flask_app,
        create_line_item_via_cash,
        create_event_via_api,
    ):
        """Test DELETE /api/events/<event_id> endpoint - success case"""
        # Create test line item via API
        create_line_item_via_cash(
            date="2009-02-13",
            person="John Doe",
            description="Test transaction",
            amount=100,
        )

        # Get created line item ID
        with flask_app.app_context():
            from dao import get_all_data

            all_line_items = get_all_data(line_items_collection)
            line_item_ids = [item["id"] for item in all_line_items]
            assert len(line_item_ids) == 1

        # Create event via API
        event_data = {
            "name": "Test Event",
            "category": "Dining",
            "date": "2009-02-13",
            "line_items": line_item_ids,
            "tags": ["test"],
            "is_duplicate_transaction": False,
        }
        event_response = create_event_via_api(event_data)
        event_id = event_response["id"]

        # Test API call
        response = test_client.delete(
            f"/api/events/{event_id}",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        assert response.get_data(as_text=True).strip() == '"Deleted Event"'

        # Verify event was deleted
        with flask_app.app_context():
            from dao import get_item_by_id

            deleted_event = get_item_by_id(events_collection, event_id)
            assert deleted_event is None

            # Verify line item event_id was removed
            line_item = get_item_by_id(line_items_collection, line_item_ids[0])
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
        self,
        test_client,
        jwt_token,
        flask_app,
        create_line_item_via_cash,
        create_event_via_api,
    ):
        """Test GET /api/events/<event_id>/line_items_for_event endpoint - success case"""
        # Create test line items via API
        create_line_item_via_cash(
            date="2009-02-13",
            person="John Doe",
            description="Transaction 1",
            amount=100,
        )
        create_line_item_via_cash(
            date="2009-02-14",
            person="Jane Smith",
            description="Transaction 2",
            amount=50,
        )

        # Get created line item IDs
        with flask_app.app_context():
            from dao import get_all_data

            all_line_items = get_all_data(line_items_collection)
            line_item_ids = [item["id"] for item in all_line_items]
            assert len(line_item_ids) == 2

        # Create event via API
        event_response = create_event_via_api(
            {
                "name": "Test Event",
                "category": "Dining",
                "date": "2009-02-13",
                "line_items": line_item_ids,
                "tags": ["test"],
                "is_duplicate_transaction": False,
            }
        )
        event_id = event_response["id"]

        # Test API call
        response = test_client.get(
            f"/api/events/{event_id}/line_items_for_event",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) == 2
        returned_ids = {item["id"] for item in data["data"]}
        assert returned_ids == set(line_item_ids)

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
        self, test_client, jwt_token, flask_app, create_line_item_via_cash
    ):
        """Test GET /api/events/<event_id>/line_items_for_event endpoint - missing line item"""
        # Create one line item via API
        create_line_item_via_cash(
            date="2009-02-13",
            person="John Doe",
            description="Transaction 1",
            amount=100,
        )

        # Get created line item ID
        with flask_app.app_context():
            from dao import get_all_data

            all_line_items = get_all_data(line_items_collection)
            line_item_ids = [item["id"] for item in all_line_items]
            assert len(line_item_ids) == 1

        # Create event via API with one real and one nonexistent line item
        # Note: We need to bypass API validation to test this edge case, use direct insert
        with flask_app.app_context():
            test_event = {
                "id": "event_test",
                "date": 1234567890,
                "name": "Test Event",
                "category": "Dining",
                "amount": 100,
                "line_items": [line_item_ids[0], "nonexistent_line_item"],
                "tags": ["test"],
            }
            upsert_with_id(events_collection, test_event, test_event["id"])

        # Test API call
        response = test_client.get(
            "/api/events/event_test/line_items_for_event",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) == 1  # Only the existing line item
        assert data["data"][0]["id"] == line_item_ids[0]

    def test_remove_event_from_line_item_different_id_types(
        self, flask_app, pg_session
    ):
        """Test remove_event_from_line_item function with different ID types"""
        from tests.test_helpers import setup_test_event, setup_test_line_item_with_event

        with flask_app.app_context():
            from dao import get_item_by_id, remove_event_from_line_item

            # Create events
            event1 = setup_test_event(
                pg_session,
                {
                    "id": "event_1",
                    "date": 1234567890,
                    "description": "Event event_1",
                    "category": "Dining",
                },
            )
            event2 = setup_test_event(
                pg_session,
                {
                    "id": "event_2",
                    "date": 1234567891,
                    "description": "Event event_2",
                    "category": "Dining",
                },
            )
            event3 = setup_test_event(
                pg_session,
                {
                    "id": "event_3",
                    "date": 1234567892,
                    "description": "Event event_3",
                    "category": "Dining",
                },
            )

            # Create line items with events - test different ID types
            setup_test_line_item_with_event(
                pg_session,
                {
                    "id": "line_item_str",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Cash",
                    "description": "Test transaction",
                    "amount": 100,
                    "event_id": "event_1",
                },
                event1.id,
            )

            setup_test_line_item_with_event(
                pg_session,
                {
                    "id": 12345,
                    "date": 1234567891,
                    "responsible_party": "Jane Smith",
                    "payment_method": "Venmo",
                    "description": "Test transaction 2",
                    "amount": 50,
                    "event_id": "event_2",
                },
                event2.id,
            )

            setup_test_line_item_with_event(
                pg_session,
                {
                    "id": "line_item_str2_uuid",
                    "date": 1234567892,
                    "responsible_party": "Bob Johnson",
                    "payment_method": "Credit Card",
                    "description": "Test transaction 3",
                    "amount": 75,
                    "event_id": "event_3",
                },
                event3.id,
            )

            pg_session.commit()

            # Verify all line items have event_id
            line_item_str = get_item_by_id(line_items_collection, "line_item_str")
            line_item_int = get_item_by_id(line_items_collection, 12345)
            line_item_str2 = get_item_by_id(
                line_items_collection, "line_item_str2_uuid"
            )

            assert line_item_str is not None
            assert line_item_int is not None
            assert line_item_str2 is not None
            assert line_item_str["event_id"] == "event_1"
            assert line_item_int["event_id"] == "event_2"
            assert line_item_str2["event_id"] == "event_3"

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

            # Test removing event_id with another string ID
            remove_event_from_line_item("line_item_str2_uuid")
            line_item_str2_after = get_item_by_id(
                line_items_collection, "line_item_str2_uuid"
            )
            assert line_item_str2_after is not None
            assert "event_id" not in line_item_str2_after


class TestEventDualWrite:
    """Test dual-write functionality for events (Phase 4)"""

    @pytest.fixture(autouse=True)
    def setup_postgres_data(self, pg_session):
        """Set up necessary PostgreSQL data for event creation"""
        # Get existing payment method (seeded by conftest.py)
        payment_method = pg_session.query(PaymentMethod).filter_by(name="Cash").first()

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
        from dao import get_collection
        from tests.test_helpers import setup_test_event, setup_test_line_item

        # Create event and line item in both databases using test helpers
        with flask_app.app_context():
            # Create line item first
            line_item_data = {
                "id": "line_item_1",
                "date": 1234567890,
                "responsible_party": "John Doe",
                "payment_method": "Cash",
                "description": "Test transaction",
                "amount": 100,
            }
            pg_line_item = setup_test_line_item(pg_session, line_item_data)

            # Create event
            event_data = {
                "id": "event_1",
                "date": 1234567890,
                "description": "Test Event",
                "category": "Dining",
                "tags": ["test"],
            }
            pg_event = setup_test_event(pg_session, event_data, line_items=[pg_line_item])

            # Manually link line item to event in MongoDB (test helpers don't do this)
            collection = get_collection(line_items_collection)
            collection.update_one({"_id": "line_item_1"}, {"$set": {"event_id": "event_1"}})

            # Update MongoDB event to include line_item in its list
            events_coll = get_collection(events_collection)
            events_coll.update_one({"_id": "event_1"}, {"$set": {"line_items": ["line_item_1"], "amount": 100}})

        # Commit the setup
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
        from dao import get_collection
        from tests.test_helpers import setup_test_event

        # Create event using test helper (avoids dual-write)
        with flask_app.app_context():
            event_data = {
                "id": "event_1",
                "date": 1234567890,
                "description": "Test Event",
                "category": "Dining",
            }
            setup_test_event(pg_session, event_data)

            # Update MongoDB event to include line_items and amount
            events_coll = get_collection(events_collection)
            events_coll.update_one({"_id": "event_1"}, {"$set": {"line_items": ["line_item_1"], "amount": 100, "tags": []}})

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

        # Create fresh session to verify deletion
        pg_session.close()
        from models.database import SessionLocal

        fresh_session = SessionLocal()
        assert (
            fresh_session.query(Event).filter(Event.mongo_id == "event_1").first()
            is None
        )
        fresh_session.close()
