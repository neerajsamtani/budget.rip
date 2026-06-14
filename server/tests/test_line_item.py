from datetime import UTC, datetime

import pytest

from resources.line_item import LineItem, all_line_items


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
        1234567890,
        "John Doe",
        "Cash",
        "Test transaction",
        100,
        id="line_item_1",
    )


class TestLineItemClass:
    def test_line_item_stores_all_transaction_fields(self, line_item_instance):
        """LineItem stores date, party, payment method, description, and amount"""
        assert line_item_instance.id == "line_item_1"
        assert line_item_instance.date == 1234567890
        assert line_item_instance.responsible_party == "John Doe"
        assert line_item_instance.payment_method == "Cash"
        assert line_item_instance.description == "Test transaction"
        assert line_item_instance.amount == 100

    def test_line_item_serializes_to_dictionary(self, line_item_instance):
        """LineItem serializes to dictionary with all fields"""
        serialized = line_item_instance.serialize()
        expected = {
            "id": "line_item_1",
            "date": 1234567890,
            "responsible_party": "John Doe",
            "payment_method": "Cash",
            "description": "Test transaction",
            "amount": 100,
        }
        assert serialized == expected

    def test_line_item_converts_to_json_string(self, line_item_instance):
        """LineItem converts to valid JSON string"""
        json_str = line_item_instance.to_json()
        # Parse back to dict to verify structure
        import json

        parsed = json.loads(json_str)
        assert parsed["id"] == "line_item_1"
        assert parsed["date"] == 1234567890
        assert parsed["responsible_party"] == "John Doe"
        assert parsed["payment_method"] == "Cash"
        assert parsed["description"] == "Test transaction"
        assert parsed["amount"] == 100

    def test_line_item_repr_includes_key_fields(self, line_item_instance):
        """LineItem repr includes ID, party, payment method, description, and amount"""
        repr_str = repr(line_item_instance)
        assert "line_item_1" in repr_str
        assert "John Doe" in repr_str
        assert "Cash" in repr_str
        assert "Test transaction" in repr_str
        assert "100" in repr_str


class TestLineItemAPI:
    def test_line_items_returns_all_items_with_total(self, test_client, jwt_token, flask_app, create_line_item_via_manual):
        """Line items endpoint returns all items with summed total"""
        # Create test line items via API
        create_line_item_via_manual(
            date="2009-02-13",
            person="John Doe",
            description="Transaction 1",
            amount=100,
        )
        create_line_item_via_manual(
            date="2009-02-14",
            person="Jane Smith",
            description="Transaction 2",
            amount=50,
        )

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

    def test_line_items_can_be_filtered_by_payment_method(
        self, test_client, jwt_token, flask_app, create_line_item_via_manual
    ):
        """Line items can be filtered by payment method"""
        # Create test line items via API (both will be Cash payment method)
        create_line_item_via_manual(
            date="2009-02-13",
            person="John Doe",
            description="Transaction 1",
            amount=100,
        )
        create_line_item_via_manual(
            date="2009-02-14",
            person="Jane Smith",
            description="Transaction 2",
            amount=50,
        )

        # Test API call with payment_method filter
        response = test_client.get(
            "/api/line_items?payment_method=Cash",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        # Both line items are Cash since they're created via cash API
        assert data["total"] == 150  # 100 + 50
        assert len(data["data"]) == 2
        assert all(item["payment_method"] == "Cash" for item in data["data"])

    def test_review_filter_excludes_line_items_with_events(
        self,
        test_client,
        jwt_token,
        flask_app,
        create_line_item_via_manual,
        create_event_via_api,
    ):
        """Review filter excludes line items already assigned to events"""
        # Create two line items via API
        create_line_item_via_manual(
            date="2009-02-13",
            person="John Doe",
            description="Transaction 1",
            amount=100,
        )
        create_line_item_via_manual(
            date="2009-02-14",
            person="Jane Smith",
            description="Transaction 2",
            amount=50,
        )

        # Get created line item IDs (sort by amount to ensure consistent ordering)
        with flask_app.app_context():
            from dao import get_all_line_items

            all_line_items = get_all_line_items()
            all_line_items_sorted = sorted(all_line_items, key=lambda x: x["amount"])
            assert len(all_line_items_sorted) == 2
            line_item_100 = all_line_items_sorted[1]  # amount=100
            line_item_50 = all_line_items_sorted[0]  # amount=50

        # Create event with the 50-amount line item (this will set event_id on that line item)
        create_event_via_api(
            {
                "name": "Test Event",
                "category": "Dining",
                "date": "2009-02-14",
                "line_items": [line_item_50["id"]],  # Only the 50-amount line item has event
                "tags": ["test"],
                "is_duplicate_transaction": False,
            }
        )

        # Test API call with review filter
        response = test_client.get(
            "/api/line_items?only_line_items_to_review=true",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 100  # Only the 100-amount line item (without event)
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == line_item_100["id"]  # Only the one without event_id

    def test_line_item_can_be_retrieved_by_id(self, test_client, flask_app, jwt_token, create_line_item_via_manual):
        """Line item can be retrieved by its ID"""
        # Create test line item via API
        create_line_item_via_manual(
            date="2009-02-13",
            person="John Doe",
            description="Test transaction",
            amount=100,
        )

        # Get created line item ID
        with flask_app.app_context():
            from dao import get_all_line_items

            all_line_items = get_all_line_items()
            assert len(all_line_items) == 1
            line_item_id = all_line_items[0]["id"]

        # Test API call
        response = test_client.get(
            f"/api/line_items/{line_item_id}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == line_item_id
        assert data["responsible_party"] == "John Doe"
        assert data["payment_method"] == "Cash"
        assert data["description"] == "Test transaction"
        assert data["amount"] == 100

    def test_nonexistent_line_item_returns_404(self, test_client, jwt_token):
        """Requesting a nonexistent line item returns 404"""
        response = test_client.get(
            "/api/line_items/nonexistent_id",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Line item not found"


class TestLineItemFunctions:
    def test_all_line_items_returns_items_sorted_by_date(self, flask_app, pg_session):
        """All line items returns items sorted by date descending"""
        from tests.test_helpers import setup_test_line_item

        with flask_app.app_context():
            test_line_items = [
                {
                    "id": "line_item_1",
                    "date": datetime(2026, 5, 29, tzinfo=UTC).timestamp(),
                    "responsible_party": "John Doe",
                    "payment_method": "Cash",
                    "description": "Test transaction 1",
                    "amount": 100,
                },
                {
                    "id": "line_item_2",
                    "date": datetime(2026, 5, 30, tzinfo=UTC).timestamp(),
                    "responsible_party": "Jane Smith",
                    "payment_method": "Venmo",
                    "description": "Test transaction 2",
                    "amount": 50,
                },
            ]

            created_items = []
            for item in test_line_items:
                created_items.append(setup_test_line_item(pg_session, item))
            pg_session.commit()

            # Test function call
            result = all_line_items()

            assert len(result) == 2
            assert result[0]["description"] == "Test transaction 2"
            assert result[1]["description"] == "Test transaction 1"
            assert result[0]["id"] == created_items[1].id
            assert result[1]["id"] == created_items[0].id

    def test_all_line_items_ignores_time_and_sorts_same_day_items_by_description(self, flask_app, pg_session):
        """All line items sorts days descending and same-day descriptions ascending"""
        from tests.test_helpers import setup_test_line_item

        with flask_app.app_context():
            test_line_items = [
                {
                    "id": "line_item_1",
                    "date": datetime(2026, 5, 29, 23, tzinfo=UTC).timestamp(),
                    "responsible_party": "John Doe",
                    "payment_method": "Cash",
                    "description": "Coffee",
                    "amount": 5,
                },
                {
                    "id": "line_item_2",
                    "date": datetime(2026, 5, 29, 1, tzinfo=UTC).timestamp(),
                    "responsible_party": "Jane Smith",
                    "payment_method": "Cash",
                    "description": "Bagels",
                    "amount": 10,
                },
                {
                    "id": "line_item_3",
                    "date": datetime(2026, 5, 30, tzinfo=UTC).timestamp(),
                    "responsible_party": "Bob Johnson",
                    "payment_method": "Cash",
                    "description": "Dinner",
                    "amount": 20,
                },
            ]

            for item in test_line_items:
                setup_test_line_item(pg_session, item)
            pg_session.commit()

            result = all_line_items()

            assert [item["description"] for item in result] == ["Dinner", "Bagels", "Coffee"]

    def test_payment_method_filter_returns_matching_items(self, flask_app, pg_session):
        """Payment method filter returns only matching line items"""
        from tests.test_helpers import setup_test_line_item

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

            created_items = []
            for item in test_line_items:
                created_items.append(setup_test_line_item(pg_session, item))
            pg_session.commit()

            # Test function call with payment_method filter
            result = all_line_items(payment_method="Cash")

            assert len(result) == 1
            assert result[0]["payment_method"] == "Cash"
            assert result[0]["description"] == "Test transaction 1"
            assert result[0]["id"] == created_items[0].id

    def test_review_filter_excludes_items_with_event_id(self, flask_app, pg_session):
        """Review filter excludes line items that have an event_id"""
        from tests.test_helpers import (
            setup_test_event,
            setup_test_line_item,
            setup_test_line_item_with_event,
        )

        with flask_app.app_context():
            # Line item without event - should be included in review
            line_item_without_event = setup_test_line_item(
                pg_session,
                {
                    "id": "line_item_1",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Cash",
                    "description": "Test transaction 1",
                    "amount": 100,
                },
            )

            # Create event first, then line item with event - should be excluded
            event = setup_test_event(
                pg_session,
                {
                    "id": "event_1",
                    "date": 1234567891,
                    "description": "Test Event",
                    "category": "Dining",
                },
            )

            setup_test_line_item_with_event(
                pg_session,
                {
                    "id": "line_item_2",
                    "date": 1234567891,
                    "responsible_party": "Jane Smith",
                    "payment_method": "Venmo",
                    "description": "Test transaction 2",
                    "amount": 50,
                    "event_id": "event_1",
                },
                event.id,
            )

            pg_session.commit()

            # Test function call with review filter
            result = all_line_items(only_line_items_to_review=True)

            assert len(result) == 1
            assert result[0]["description"] == "Test transaction 1"
            assert result[0]["id"] == line_item_without_event.id

    def test_payment_method_and_review_filters_combine(self, flask_app, pg_session):
        """Payment method and review filters can be combined"""
        from tests.test_helpers import (
            setup_test_event,
            setup_test_line_item,
            setup_test_line_item_with_event,
        )

        with flask_app.app_context():
            # Cash without event - should be included
            cash_without_event = setup_test_line_item(
                pg_session,
                {
                    "id": "line_item_1",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Cash",
                    "description": "Test transaction 1",
                    "amount": 100,
                },
            )

            # Venmo without event - should be excluded (payment_method filter)
            setup_test_line_item(
                pg_session,
                {
                    "id": "line_item_2",
                    "date": 1234567891,
                    "responsible_party": "Jane Smith",
                    "payment_method": "Venmo",
                    "description": "Test transaction 2",
                    "amount": 50,
                },
            )

            # Cash with event - should be excluded (review filter)
            event = setup_test_event(
                pg_session,
                {
                    "id": "event_1",
                    "date": 1234567892,
                    "description": "Test Event",
                    "category": "Dining",
                },
            )

            setup_test_line_item_with_event(
                pg_session,
                {
                    "id": "line_item_3",
                    "date": 1234567892,
                    "responsible_party": "Bob Johnson",
                    "payment_method": "Cash",
                    "description": "Test transaction 3",
                    "amount": 75,
                    "event_id": "event_1",
                },
                event.id,
            )

            pg_session.commit()

            # Test function call with both filters
            result = all_line_items(payment_method="Cash", only_line_items_to_review=True)

            assert len(result) == 1
            assert result[0]["description"] == "Test transaction 1"
            assert result[0]["id"] == cash_without_event.id

    def test_empty_database_returns_empty_list(self, flask_app):
        """Empty database returns empty line items list"""
        with flask_app.app_context():
            # Test function call with no data in database
            result = all_line_items()

            assert len(result) == 0

    def test_payment_method_all_returns_all_items(self, flask_app, pg_session):
        """Payment method 'All' returns all line items"""
        from tests.test_helpers import setup_test_line_item

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
                setup_test_line_item(pg_session, item)
            pg_session.commit()

            # Test function call with payment_method='All'
            result = all_line_items(payment_method="All")

            assert len(result) == 2  # Should return all items, same as no filter

    def test_limit_restricts_number_of_returned_items(self, flask_app, pg_session):
        """Limit parameter restricts the number of line items returned"""
        from tests.test_helpers import setup_test_line_item

        with flask_app.app_context():
            # Use distinct days so DB date order matches final sorted order
            for i in range(5):
                setup_test_line_item(
                    pg_session,
                    {
                        "id": f"line_item_{i}",
                        "date": 1234567890 + i * 86400,
                        "responsible_party": "John Doe",
                        "payment_method": "Cash",
                        "description": f"Transaction {i}",
                        "amount": 10 * (i + 1),
                    },
                )
            pg_session.commit()

            result = all_line_items(limit=3)

            assert len(result) == 3

    def test_offset_skips_leading_items(self, flask_app, pg_session):
        """Offset parameter skips the first N line items"""
        from tests.test_helpers import setup_test_line_item

        with flask_app.app_context():
            # Use distinct days so DB date order matches final sorted order
            for i in range(5):
                setup_test_line_item(
                    pg_session,
                    {
                        "id": f"line_item_{i}",
                        "date": 1234567890 + i * 86400,
                        "responsible_party": "John Doe",
                        "payment_method": "Cash",
                        "description": f"Transaction {i}",
                        "amount": 10 * (i + 1),
                    },
                )
            pg_session.commit()

            all_result = all_line_items()
            paged_result = all_line_items(offset=2)

            assert len(paged_result) == 3
            assert paged_result[0]["id"] == all_result[2]["id"]

    def test_limit_and_offset_together_return_correct_page(self, flask_app, pg_session):
        """Limit and offset together select a specific page of results"""
        from tests.test_helpers import setup_test_line_item

        with flask_app.app_context():
            # Use distinct days so DB date order matches final sorted order
            for i in range(5):
                setup_test_line_item(
                    pg_session,
                    {
                        "id": f"line_item_{i}",
                        "date": 1234567890 + i * 86400,
                        "responsible_party": "John Doe",
                        "payment_method": "Cash",
                        "description": f"Transaction {i}",
                        "amount": 10 * (i + 1),
                    },
                )
            pg_session.commit()

            all_result = all_line_items()
            page2 = all_line_items(limit=2, offset=2)

            assert len(page2) == 2
            assert page2[0]["id"] == all_result[2]["id"]
            assert page2[1]["id"] == all_result[3]["id"]

    def test_limit_via_api_restricts_returned_items(self, test_client, jwt_token, create_line_item_via_manual):
        """GET /api/line_items?limit=N returns at most N line items"""
        for i in range(4):
            create_line_item_via_manual(
                date="2009-02-13",
                person="John Doe",
                description=f"Transaction {i}",
                amount=10,
            )

        response = test_client.get(
            "/api/line_items?limit=2",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) == 2

    def test_offset_via_api_skips_leading_items(self, test_client, jwt_token, create_line_item_via_manual):
        """GET /api/line_items?offset=N skips the first N line items"""
        for i in range(4):
            create_line_item_via_manual(
                date="2009-02-13",
                person="John Doe",
                description=f"Transaction {i}",
                amount=10,
            )

        full_response = test_client.get(
            "/api/line_items",
            headers={"Authorization": "Bearer " + jwt_token},
        )
        paged_response = test_client.get(
            "/api/line_items?offset=2",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert paged_response.status_code == 200
        full_data = full_response.get_json()["data"]
        paged_data = paged_response.get_json()["data"]
        assert len(paged_data) == 2
        assert paged_data[0]["id"] == full_data[2]["id"]
