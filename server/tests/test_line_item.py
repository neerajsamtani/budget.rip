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

            all_line_items = get_all_line_items(None)
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

            all_line_items = get_all_line_items(None)
            assert len(all_line_items) == 1
            line_item_id = all_line_items[0]["id"]

        # Test API call
        response = test_client.get(
            f"/api/line_items/{line_item_id}",
            headers={"Authorization": "Bearer " + jwt_token},
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
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Line item not found"

    def test_line_item_notes_can_be_updated(self, test_client, jwt_token, flask_app, create_line_item_via_manual):
        """Line item notes can be updated via PATCH"""
        create_line_item_via_manual(
            date="2009-02-13",
            person="John Doe",
            description="Test transaction",
            amount=100,
        )

        with flask_app.app_context():
            from dao import get_all_line_items

            all_line_items = get_all_line_items(None)
            assert len(all_line_items) == 1
            line_item_id = all_line_items[0]["id"]

        response = test_client.patch(
            f"/api/line_items/{line_item_id}",
            headers={"Authorization": "Bearer " + jwt_token},
            json={"notes": "Test note content"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["notes"] == "Test note content"
        assert data["message"] == "Line item updated"

    def test_line_item_notes_can_be_cleared(self, test_client, jwt_token, flask_app, create_line_item_via_manual):
        """Line item notes can be cleared by setting to empty string"""
        create_line_item_via_manual(
            date="2009-02-13",
            person="John Doe",
            description="Test transaction",
            amount=100,
        )

        with flask_app.app_context():
            from dao import get_all_line_items

            all_line_items = get_all_line_items(None)
            line_item_id = all_line_items[0]["id"]

        # First set notes
        test_client.patch(
            f"/api/line_items/{line_item_id}",
            headers={"Authorization": "Bearer " + jwt_token},
            json={"notes": "Some notes"},
        )

        # Then clear them
        response = test_client.patch(
            f"/api/line_items/{line_item_id}",
            headers={"Authorization": "Bearer " + jwt_token},
            json={"notes": ""},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["notes"] == ""

    def test_update_nonexistent_line_item_returns_404(self, test_client, jwt_token):
        """PATCH on non-existent line item returns 404"""
        response = test_client.patch(
            "/api/line_items/nonexistent_id",
            headers={"Authorization": "Bearer " + jwt_token},
            json={"notes": "Test notes"},
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Line item not found"

    def test_update_with_invalid_fields_returns_400(self, test_client, jwt_token, flask_app, create_line_item_via_manual):
        """PATCH with invalid fields returns 400"""
        create_line_item_via_manual(
            date="2009-02-13",
            person="John Doe",
            description="Test transaction",
            amount=100,
        )

        with flask_app.app_context():
            from dao import get_all_line_items

            all_line_items = get_all_line_items(None)
            line_item_id = all_line_items[0]["id"]

        response = test_client.patch(
            f"/api/line_items/{line_item_id}",
            headers={"Authorization": "Bearer " + jwt_token},
            json={"notes": "Valid", "amount": 999, "description": "Invalid"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid fields" in data["error"]

    def test_update_line_item_requires_authentication(self, test_client, flask_app, create_line_item_via_manual, jwt_token):
        """PATCH requires authentication"""
        create_line_item_via_manual(
            date="2009-02-13",
            person="John Doe",
            description="Test transaction",
            amount=100,
        )

        with flask_app.app_context():
            from dao import get_all_line_items

            all_line_items = get_all_line_items(None)
            line_item_id = all_line_items[0]["id"]

        response = test_client.patch(
            f"/api/line_items/{line_item_id}",
            json={"notes": "Test notes"},
        )

        assert response.status_code == 401


class TestLineItemFunctions:
    def test_all_line_items_returns_items_sorted_by_date(self, flask_app, pg_session):
        """All line items returns items sorted by date descending"""
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

            # Test function call
            result = all_line_items()

            assert len(result) == 2
            assert result[0]["description"] == "Test transaction 2"
            assert result[1]["description"] == "Test transaction 1"
            assert result[0]["id"] == created_items[1].id
            assert result[1]["id"] == created_items[0].id

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


class TestLineItemBankAccountSerialization:
    def test_bank_payment_with_external_id_includes_bank_account(self, flask_app, pg_session):
        """Line item with bank payment method and external_id includes bank_account in serialization"""
        from models.sql_models import BankAccount, PaymentMethod

        with flask_app.app_context():
            # Create a bank account
            bank_account = BankAccount(
                id="fca_test123",
                institution_name="Chase",
                display_name="Chase Checking",
                last4="1234",
                status="active",
            )
            pg_session.add(bank_account)
            pg_session.flush()

            # Update the Debit Card payment method to have external_id
            pm = pg_session.query(PaymentMethod).filter(PaymentMethod.name == "Debit Card").first()
            pm.external_id = "fca_test123"
            pg_session.flush()

            # Create a line item with Debit Card payment method
            from tests.test_helpers import setup_test_line_item

            setup_test_line_item(
                pg_session,
                {
                    "id": "line_item_bank",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Debit Card",
                    "description": "Bank transaction",
                    "amount": 100,
                },
            )
            pg_session.commit()

            # Test serialization
            result = all_line_items()

            assert len(result) == 1
            assert result[0]["payment_method_type"] == "bank"
            assert "bank_account" in result[0]
            assert result[0]["bank_account"]["institution_name"] == "Chase"
            assert result[0]["bank_account"]["display_name"] == "Chase Checking"
            assert result[0]["bank_account"]["last4"] == "1234"

    def test_credit_payment_with_external_id_includes_bank_account(self, flask_app, pg_session):
        """Line item with credit payment method and external_id includes bank_account in serialization"""
        from models.sql_models import BankAccount, PaymentMethod

        with flask_app.app_context():
            # Create a bank account for the credit card
            bank_account = BankAccount(
                id="fca_credit456",
                institution_name="Amex",
                display_name="Amex Gold",
                last4="9999",
                status="active",
            )
            pg_session.add(bank_account)
            pg_session.flush()

            # Update the Credit Card payment method to have external_id
            pm = pg_session.query(PaymentMethod).filter(PaymentMethod.name == "Credit Card").first()
            pm.external_id = "fca_credit456"
            pg_session.flush()

            # Create a line item with Credit Card payment method
            from tests.test_helpers import setup_test_line_item

            setup_test_line_item(
                pg_session,
                {
                    "id": "line_item_credit",
                    "date": 1234567890,
                    "responsible_party": "Jane Smith",
                    "payment_method": "Credit Card",
                    "description": "Credit card transaction",
                    "amount": 200,
                },
            )
            pg_session.commit()

            # Test serialization
            result = all_line_items()

            assert len(result) == 1
            assert result[0]["payment_method_type"] == "credit"
            assert "bank_account" in result[0]
            assert result[0]["bank_account"]["institution_name"] == "Amex"
            assert result[0]["bank_account"]["display_name"] == "Amex Gold"
            assert result[0]["bank_account"]["last4"] == "9999"

    def test_non_bank_payment_excludes_bank_account(self, flask_app, pg_session):
        """Line item with non-bank payment method (venmo/cash) excludes bank_account"""
        from tests.test_helpers import setup_test_line_item

        with flask_app.app_context():
            # Create line items with Venmo and Cash payment methods
            setup_test_line_item(
                pg_session,
                {
                    "id": "line_item_venmo",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Venmo",
                    "description": "Venmo transaction",
                    "amount": 50,
                },
            )
            setup_test_line_item(
                pg_session,
                {
                    "id": "line_item_cash",
                    "date": 1234567891,
                    "responsible_party": "Jane Smith",
                    "payment_method": "Cash",
                    "description": "Cash transaction",
                    "amount": 25,
                },
            )
            pg_session.commit()

            # Test serialization
            result = all_line_items()

            assert len(result) == 2
            for item in result:
                assert item["payment_method_type"] in ("venmo", "cash")
                assert "bank_account" not in item

    def test_bank_payment_without_external_id_excludes_bank_account(self, flask_app, pg_session):
        """Line item with bank payment but no external_id excludes bank_account"""
        from tests.test_helpers import setup_test_line_item

        with flask_app.app_context():
            # Debit Card has type "bank" but no external_id by default
            setup_test_line_item(
                pg_session,
                {
                    "id": "line_item_debit",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Debit Card",
                    "description": "Debit transaction",
                    "amount": 100,
                },
            )
            pg_session.commit()

            # Test serialization
            result = all_line_items()

            assert len(result) == 1
            assert result[0]["payment_method_type"] == "bank"
            assert "bank_account" not in result[0]

    def test_bank_payment_with_invalid_external_id_excludes_bank_account(self, flask_app, pg_session):
        """Line item with bank payment but invalid external_id (no matching bank account) excludes bank_account"""
        from models.sql_models import PaymentMethod
        from tests.test_helpers import setup_test_line_item

        with flask_app.app_context():
            # Set external_id to a non-existent bank account
            pm = pg_session.query(PaymentMethod).filter(PaymentMethod.name == "Debit Card").first()
            pm.external_id = "fca_nonexistent"
            pg_session.flush()

            setup_test_line_item(
                pg_session,
                {
                    "id": "line_item_debit",
                    "date": 1234567890,
                    "responsible_party": "John Doe",
                    "payment_method": "Debit Card",
                    "description": "Debit transaction",
                    "amount": 100,
                },
            )
            pg_session.commit()

            # Test serialization - should not crash and should exclude bank_account
            result = all_line_items()

            assert len(result) == 1
            assert result[0]["payment_method_type"] == "bank"
            assert "bank_account" not in result[0]
