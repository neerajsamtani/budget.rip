import pytest

from dao import events_collection, line_items_collection, upsert_with_id


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
    def test_events_returns_all_events_with_total_amount(
        self,
        test_client,
        jwt_token,
        flask_app,
        create_line_item_via_cash,
        create_event_via_api,
    ):
        """Events endpoint returns all events with summed total amount"""
        # Create test line items via API
        create_line_item_via_cash(date="2009-02-13", person="Person1", description="Transaction 1", amount=100)
        create_line_item_via_cash(date="2009-02-14", person="Person2", description="Transaction 2", amount=50)

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

    def test_events_can_be_filtered_by_date_range(
        self,
        test_client,
        jwt_token,
        flask_app,
        create_line_item_via_cash,
        create_event_via_api,
    ):
        """Events can be filtered by start_time and end_time"""
        # Create test line items via API
        create_line_item_via_cash(date="2009-02-13", person="Person1", description="Transaction 1", amount=100)
        create_line_item_via_cash(date="2009-02-14", person="Person2", description="Transaction 2", amount=50)

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

    def test_event_can_be_retrieved_by_id(
        self,
        test_client,
        jwt_token,
        flask_app,
        create_line_item_via_cash,
        create_event_via_api,
    ):
        """Event can be retrieved by its ID"""
        # Create test line item via API
        create_line_item_via_cash(date="2009-02-13", person="Person1", description="Transaction 1", amount=100)

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

    def test_nonexistent_event_returns_404(self, test_client, jwt_token):
        """Requesting a nonexistent event returns 404"""
        response = test_client.get(
            "/api/events/nonexistent_id",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Event not found"

    def test_event_creation_calculates_total_amount(self, test_client, jwt_token, flask_app, create_line_item_via_cash):
        """Creating an event links line items and calculates total amount"""
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

    def test_event_creation_requires_line_items(self, test_client, jwt_token):
        """Creating an event requires at least one line item"""
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
        assert response.get_data(as_text=True).strip() == '"Failed to Create Event: No Line Items Submitted"'

    def test_duplicate_flag_uses_first_line_item_amount(self, test_client, jwt_token, flask_app, create_line_item_via_cash):
        """Duplicate transaction events use only the first line item amount"""
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

    def test_event_uses_earliest_line_item_date(self, test_client, jwt_token, flask_app, create_line_item_via_cash):
        """Event uses earliest line item date when date is not provided"""
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
            assert created_event["date"] == all_line_items[0]["date"]  # Should use earliest line item date

    def test_deleting_event_unlinks_line_items(
        self,
        test_client,
        jwt_token,
        flask_app,
        create_line_item_via_cash,
        create_event_via_api,
    ):
        """Deleting an event removes event_id from associated line items"""
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

    def test_deleting_nonexistent_event_returns_404(self, test_client, jwt_token):
        """Deleting a nonexistent event returns 404"""
        response = test_client.delete(
            "/api/events/nonexistent_id",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Event not found"

    def test_updating_event_modifies_name_category_and_line_items(
        self,
        test_client,
        jwt_token,
        flask_app,
        create_line_item_via_cash,
        create_event_via_api,
    ):
        """Updating an event can change name, category, and line items"""
        # Create test line items via API
        create_line_item_via_cash(date="2009-02-13", person="Person1", description="Transaction 1", amount=100)
        create_line_item_via_cash(date="2009-02-14", person="Person2", description="Transaction 2", amount=50)

        # Get created line item IDs
        with flask_app.app_context():
            from dao import get_all_data

            all_line_items = get_all_data(line_items_collection)
            line_item_ids = [item["id"] for item in all_line_items]
            assert len(line_item_ids) == 2

        # Create event via API
        event_response = create_event_via_api(
            {
                "name": "Original Event",
                "category": "Dining",
                "date": "2009-02-13",
                "line_items": [line_item_ids[0]],
                "tags": ["original"],
                "is_duplicate_transaction": False,
            }
        )
        event_id = event_response["id"]

        # Update event via API
        update_data = {
            "name": "Updated Event",
            "category": "Shopping",
            "line_items": line_item_ids,  # Add both line items
            "tags": ["updated", "modified"],
            "is_duplicate_transaction": False,
        }

        response = test_client.put(
            f"/api/events/{event_id}",
            json=update_data,
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data["name"] == "Updated Event"
        assert response_data["category"] == "Shopping"
        assert response_data["amount"] == 150  # 100 + 50
        assert set(response_data["line_items"]) == set(line_item_ids)
        assert set(response_data["tags"]) == {"updated", "modified"}

        # Verify event was updated in database
        with flask_app.app_context():
            from dao import get_item_by_id

            updated_event = get_item_by_id(events_collection, event_id)
            assert updated_event is not None
            assert updated_event["name"] == "Updated Event"
            assert updated_event["category"] == "Shopping"

    def test_updating_nonexistent_event_returns_404(self, test_client, jwt_token):
        """Updating a nonexistent event returns 404"""
        update_data = {
            "name": "Updated Event",
            "category": "Shopping",
            "line_items": ["some_id"],
        }

        response = test_client.put(
            "/api/events/nonexistent_id",
            json=update_data,
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Event not found"

    def test_updating_event_to_zero_line_items_fails(
        self,
        test_client,
        jwt_token,
        flask_app,
        create_line_item_via_cash,
        create_event_via_api,
    ):
        """Event update fails when removing all line items"""
        # Create test line item via API
        create_line_item_via_cash(date="2009-02-13", person="Person1", description="Transaction 1", amount=100)

        # Get created line item ID
        with flask_app.app_context():
            from dao import get_all_data

            all_line_items = get_all_data(line_items_collection)
            line_item_ids = [item["id"] for item in all_line_items]

        # Create event via API
        event_response = create_event_via_api(
            {
                "name": "Original Event",
                "category": "Dining",
                "date": "2009-02-13",
                "line_items": line_item_ids,
                "tags": [],
                "is_duplicate_transaction": False,
            }
        )
        event_id = event_response["id"]

        # Try to update with no line items
        update_data = {
            "name": "Updated Event",
            "category": "Shopping",
            "line_items": [],
        }

        response = test_client.put(
            f"/api/events/{event_id}",
            json=update_data,
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Event must have at least one line item"

    def test_event_line_items_returns_associated_line_items(
        self,
        test_client,
        jwt_token,
        flask_app,
        create_line_item_via_cash,
        create_event_via_api,
    ):
        """Event line items endpoint returns all line items for an event"""
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

    def test_line_items_for_nonexistent_event_returns_404(self, test_client, jwt_token):
        """Requesting line items for nonexistent event returns 404"""
        response = test_client.get(
            "/api/events/nonexistent_id/line_items_for_event",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Event not found"

    def test_missing_line_items_are_skipped_in_response(self, test_client, jwt_token, flask_app, create_line_item_via_cash):
        """Missing line items are skipped when retrieving event line items"""
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

            # Get the actual PostgreSQL event ID that was created
            all_events = get_all_data(events_collection)
            assert len(all_events) == 1
            actual_event_id = all_events[0]["id"]

        # Test API call with actual PostgreSQL event ID
        response = test_client.get(
            f"/api/events/{actual_event_id}/line_items_for_event",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) == 1  # Only the existing line item
        assert data["data"][0]["id"] == line_item_ids[0]

    def test_event_removal_clears_event_id_from_line_items(self, flask_app, pg_session):
        """Removing event from line items clears event_id regardless of ID type"""
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

            # Create line items with events - capture the actual PostgreSQL objects
            line_item1 = setup_test_line_item_with_event(
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

            line_item2 = setup_test_line_item_with_event(
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

            line_item3 = setup_test_line_item_with_event(
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

            # Verify all line items have event_id using actual PostgreSQL IDs
            line_item_data1 = get_item_by_id(line_items_collection, line_item1.id)
            line_item_data2 = get_item_by_id(line_items_collection, line_item2.id)
            line_item_data3 = get_item_by_id(line_items_collection, line_item3.id)

            assert line_item_data1 is not None
            assert line_item_data2 is not None
            assert line_item_data3 is not None
            assert line_item_data1["event_id"] == event1.id
            assert line_item_data2["event_id"] == event2.id
            assert line_item_data3["event_id"] == event3.id

            # Test removing event_id from first line item
            remove_event_from_line_item(line_item1.id)
            line_item_data1_after = get_item_by_id(line_items_collection, line_item1.id)
            assert line_item_data1_after is not None
            assert "event_id" not in line_item_data1_after

            # Test removing event_id from second line item
            remove_event_from_line_item(line_item2.id)
            line_item_data2_after = get_item_by_id(line_items_collection, line_item2.id)
            assert line_item_data2_after is not None
            assert "event_id" not in line_item_data2_after

            # Test removing event_id from third line item
            remove_event_from_line_item(line_item3.id)
            line_item_data3_after = get_item_by_id(line_items_collection, line_item3.id)
            assert line_item_data3_after is not None
            assert "event_id" not in line_item_data3_after
