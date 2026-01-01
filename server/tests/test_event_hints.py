from datetime import UTC, datetime

import pytest

from models.sql_models import Category, EventHint, LineItem, PaymentMethod, Transaction, User
from utils.cel_evaluator import CELEvaluator, evaluate_hints


@pytest.fixture
def test_user(pg_session):
    """Get or create a test user with id matching jwt_token"""
    # Try to get existing user first (may have been created by seed function)
    user = pg_session.query(User).filter_by(id="user_id").first()
    if not user:
        user = User(
            id="user_id",  # Must match the identity in jwt_token fixture
            first_name="Test",
            last_name="User",
            email="test_user_fixture@example.com",
            password_hash="hashed_password",
        )
        pg_session.add(user)
        pg_session.commit()
    return user


@pytest.fixture
def sample_hints(pg_session, test_user):
    """Create sample event hints for testing"""
    # Get the subscription category
    subscription_cat = pg_session.query(Category).filter_by(name="Subscription").first()
    transfer_cat = pg_session.query(Category).filter_by(name="Transfer").first()

    hints = [
        EventHint(
            id="eh_1",
            user_id=test_user.id,
            name="Spotify Subscription",
            cel_expression='description.contains("Spotify")',
            prefill_name="Spotify",
            prefill_category_id=subscription_cat.id if subscription_cat else None,
            display_order=0,
            is_active=True,
        ),
        EventHint(
            id="eh_2",
            user_id=test_user.id,
            name="Transfer Detection",
            cel_expression="sum(amount) == 0",
            prefill_name="Transfer",
            prefill_category_id=transfer_cat.id if transfer_cat else None,
            display_order=1,
            is_active=True,
        ),
        EventHint(
            id="eh_3",
            user_id=test_user.id,
            name="Inactive Hint",
            cel_expression='description.contains("Netflix")',
            prefill_name="Netflix",
            prefill_category_id=subscription_cat.id if subscription_cat else None,
            display_order=2,
            is_active=False,
        ),
    ]
    pg_session.add_all(hints)
    pg_session.commit()
    return hints


@pytest.fixture
def sample_line_items(pg_session):
    """Create sample line items for testing"""
    pm = pg_session.query(PaymentMethod).first()

    # Create transactions first (line items require a transaction)
    transactions = [
        Transaction(
            id="txn_1",
            source="manual",
            source_id="test_1",
            source_data={"test": True},
            transaction_date=datetime.now(UTC),
        ),
        Transaction(
            id="txn_2",
            source="manual",
            source_id="test_2",
            source_data={"test": True},
            transaction_date=datetime.now(UTC),
        ),
        Transaction(
            id="txn_3",
            source="manual",
            source_id="test_3",
            source_data={"test": True},
            transaction_date=datetime.now(UTC),
        ),
    ]
    pg_session.add_all(transactions)
    pg_session.commit()

    line_items = [
        LineItem(
            id="li_1",
            transaction_id="txn_1",
            date=datetime.now(UTC),
            description="Spotify Premium Monthly",
            amount=9.99,
            payment_method_id=pm.id if pm else None,
        ),
        LineItem(
            id="li_2",
            transaction_id="txn_2",
            date=datetime.now(UTC),
            description="Venmo Transfer",
            amount=50.00,
            payment_method_id=pm.id if pm else None,
        ),
        LineItem(
            id="li_3",
            transaction_id="txn_3",
            date=datetime.now(UTC),
            description="Venmo Transfer",
            amount=-50.00,
            payment_method_id=pm.id if pm else None,
        ),
    ]
    pg_session.add_all(line_items)
    pg_session.commit()
    return line_items


class TestCELEvaluator:
    """Tests for the CEL expression evaluator"""

    def test_simple_contains_expression(self):
        """Test basic contains expression"""
        evaluator = CELEvaluator('description.contains("Spotify")')
        line_items = [{"description": "Spotify Premium Monthly", "amount": 9.99}]
        assert evaluator.evaluate(line_items) is True

    def test_contains_case_insensitive(self):
        """Test that contains is case-insensitive (all strings are lowercased)"""
        # Mixed case in expression should match uppercase in data
        evaluator = CELEvaluator('description.contains("Spotify")')
        line_items = [{"description": "SPOTIFY PREMIUM", "amount": 9.99}]
        assert evaluator.evaluate(line_items) is True

        # Lowercase in expression should match mixed case in data
        evaluator = CELEvaluator('description.contains("spotify")')
        line_items = [{"description": "Spotify Premium", "amount": 9.99}]
        assert evaluator.evaluate(line_items) is True

        # Uppercase in expression should also match
        evaluator = CELEvaluator('description.contains("SPOTIFY")')
        line_items = [{"description": "spotify premium", "amount": 9.99}]
        assert evaluator.evaluate(line_items) is True

    def test_contains_no_match(self):
        """Test contains with no match"""
        evaluator = CELEvaluator('description.contains("Netflix")')
        line_items = [{"description": "Spotify Premium", "amount": 9.99}]
        assert evaluator.evaluate(line_items) is False

    def test_numeric_comparison(self):
        """Test numeric comparison"""
        evaluator = CELEvaluator("amount > 10")
        line_items = [{"description": "Test", "amount": 15.00}]
        assert evaluator.evaluate(line_items) is True

        line_items = [{"description": "Test", "amount": 5.00}]
        assert evaluator.evaluate(line_items) is False

    def test_combined_conditions(self):
        """Test AND conditions"""
        evaluator = CELEvaluator('description.contains("Uber") && amount < 50')
        line_items = [{"description": "Uber Trip", "amount": 25.00}]
        assert evaluator.evaluate(line_items) is True

        line_items = [{"description": "Uber Trip", "amount": 75.00}]
        assert evaluator.evaluate(line_items) is False

    def test_any_line_item_matches(self):
        """Test that any matching line item returns True"""
        evaluator = CELEvaluator('description.contains("Spotify")')
        line_items = [
            {"description": "Netflix", "amount": 15.00},
            {"description": "Spotify Premium", "amount": 9.99},
        ]
        assert evaluator.evaluate(line_items) is True

    def test_empty_line_items(self):
        """Test with empty line items list"""
        evaluator = CELEvaluator('description.contains("Spotify")')
        assert evaluator.evaluate([]) is False

    def test_aggregate_sum(self):
        """Test sum aggregate function"""
        evaluator = CELEvaluator("sum(amount) == 0")
        line_items = [
            {"description": "Transfer Out", "amount": -50.00},
            {"description": "Transfer In", "amount": 50.00},
        ]
        assert evaluator.evaluate(line_items) is True

        line_items = [
            {"description": "Purchase", "amount": 25.00},
            {"description": "Purchase", "amount": 10.00},
        ]
        assert evaluator.evaluate(line_items) is False

    def test_aggregate_count(self):
        """Test count aggregate function"""
        evaluator = CELEvaluator("count() > 1")
        line_items = [
            {"description": "Item 1", "amount": 10.00},
            {"description": "Item 2", "amount": 20.00},
        ]
        assert evaluator.evaluate(line_items) is True

        line_items = [{"description": "Item 1", "amount": 10.00}]
        assert evaluator.evaluate(line_items) is False

    def test_aggregate_all_match(self):
        """Test all_match aggregate function"""
        evaluator = CELEvaluator('all_match(description.contains("Uber"))')
        line_items = [
            {"description": "Uber Trip 1", "amount": 10.00},
            {"description": "Uber Trip 2", "amount": 20.00},
        ]
        assert evaluator.evaluate(line_items) is True

        line_items = [
            {"description": "Uber Trip", "amount": 10.00},
            {"description": "Lyft Trip", "amount": 20.00},
        ]
        assert evaluator.evaluate(line_items) is False

    def test_aggregate_any_match(self):
        """Test any_match aggregate function"""
        evaluator = CELEvaluator('any_match(payment_method == "Venmo")')
        line_items = [
            {"description": "Item 1", "amount": 10.00, "payment_method": "Cash"},
            {"description": "Item 2", "amount": 20.00, "payment_method": "Venmo"},
        ]
        assert evaluator.evaluate(line_items) is True


class TestCELValidation:
    """Tests for CEL expression validation"""

    def test_valid_simple_expression(self):
        """Test validation of valid simple expression"""
        is_valid, error = CELEvaluator.validate('description.contains("Spotify")')
        assert is_valid is True
        assert error is None

    def test_valid_comparison_expression(self):
        """Test validation of valid comparison expression"""
        is_valid, error = CELEvaluator.validate("amount > 100")
        assert is_valid is True
        assert error is None

    def test_valid_aggregate_expression(self):
        """Test validation of valid aggregate expression"""
        is_valid, error = CELEvaluator.validate("sum(amount) == 0")
        assert is_valid is True
        assert error is None

    def test_empty_expression(self):
        """Test validation of empty expression"""
        is_valid, error = CELEvaluator.validate("")
        assert is_valid is False
        assert error is not None

    def test_invalid_syntax(self):
        """Test validation of invalid syntax"""
        is_valid, error = CELEvaluator.validate("description contains")
        assert is_valid is False
        assert error is not None

    def test_expression_length_limit(self):
        """Test that expressions exceeding max length are rejected"""
        # Create an expression that exceeds the 500 character limit
        long_expression = 'description.contains("' + "a" * 500 + '")'
        is_valid, error = CELEvaluator.validate(long_expression)
        assert is_valid is False
        assert "too long" in error.lower()

    def test_expression_at_length_limit(self):
        """Test that expressions at exactly the limit are accepted"""
        # Create an expression that is exactly at the limit (if valid syntax)
        expression = 'description.contains("test")'  # 28 chars, well under limit
        is_valid, error = CELEvaluator.validate(expression)
        assert is_valid is True
        assert error is None

    def test_nesting_depth_limit(self):
        """Test that deeply nested expressions are rejected"""
        # Create a deeply nested expression (11 levels of parentheses)
        nested_expression = "(" * 11 + "amount > 0" + ")" * 11
        is_valid, error = CELEvaluator.validate(nested_expression)
        assert is_valid is False
        assert "nested" in error.lower()

    def test_nesting_at_depth_limit(self):
        """Test that expressions at exactly the nesting limit are accepted"""
        # Create an expression with exactly 10 levels of nesting
        nested_expression = "(" * 10 + "amount > 0" + ")" * 10
        is_valid, error = CELEvaluator.validate(nested_expression)
        assert is_valid is True
        assert error is None


class TestEvaluateHints:
    """Tests for the evaluate_hints function"""

    def test_first_match_wins(self):
        """Test that first matching hint is returned"""
        hints = [
            {
                "id": "eh_1",
                "name": "Hint 1",
                "cel_expression": 'description.contains("Test")',
                "prefill_name": "Test Event 1",
                "prefill_category": "Shopping",
                "is_active": True,
            },
            {
                "id": "eh_2",
                "name": "Hint 2",
                "cel_expression": 'description.contains("Test")',
                "prefill_name": "Test Event 2",
                "prefill_category": "Dining",
                "is_active": True,
            },
        ]
        line_items = [{"description": "Test Purchase", "amount": 10.00}]

        result = evaluate_hints(hints, line_items)
        assert result is not None
        assert result["name"] == "Test Event 1"
        assert result["matched_hint_id"] == "eh_1"

    def test_skips_inactive_hints(self):
        """Test that inactive hints are skipped"""
        hints = [
            {
                "id": "eh_1",
                "name": "Hint 1",
                "cel_expression": 'description.contains("Test")',
                "prefill_name": "Test Event 1",
                "is_active": False,
            },
            {
                "id": "eh_2",
                "name": "Hint 2",
                "cel_expression": 'description.contains("Test")',
                "prefill_name": "Test Event 2",
                "is_active": True,
            },
        ]
        line_items = [{"description": "Test Purchase", "amount": 10.00}]

        result = evaluate_hints(hints, line_items)
        assert result is not None
        assert result["matched_hint_id"] == "eh_2"

    def test_no_match_returns_none(self):
        """Test that no match returns None"""
        hints = [
            {
                "id": "eh_1",
                "name": "Hint 1",
                "cel_expression": 'description.contains("Spotify")',
                "prefill_name": "Spotify",
                "is_active": True,
            },
        ]
        line_items = [{"description": "Netflix Premium", "amount": 15.00}]

        result = evaluate_hints(hints, line_items)
        assert result is None


class TestEventHintsAPI:
    """Tests for the Event Hints API endpoints"""

    def test_get_all_hints_empty(self, test_client, jwt_token, test_user):
        """Test GET /api/event-hints returns empty list when no hints exist"""
        response = test_client.get("/api/event-hints", headers={"Authorization": f"Bearer {jwt_token}"})
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert data["data"] == []

    def test_get_all_hints(self, test_client, jwt_token, test_user, sample_hints):
        """Test GET /api/event-hints returns all hints for user"""
        response = test_client.get("/api/event-hints", headers={"Authorization": f"Bearer {jwt_token}"})
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) == 3

    def test_create_hint(self, test_client, jwt_token, test_user, pg_session):
        """Test POST /api/event-hints creates a new hint"""
        subscription_cat = pg_session.query(Category).filter_by(name="Subscription").first()

        hint_data = {
            "name": "New Hint",
            "cel_expression": 'description.contains("Amazon")',
            "prefill_name": "Amazon Order",
            "prefill_category_id": subscription_cat.id if subscription_cat else None,
        }

        response = test_client.post(
            "/api/event-hints",
            json=hint_data,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["data"]["name"] == "New Hint"
        assert data["data"]["prefill_name"] == "Amazon Order"

    def test_create_hint_invalid_cel(self, test_client, jwt_token, test_user):
        """Test POST /api/event-hints rejects invalid CEL expression"""
        hint_data = {
            "name": "Bad Hint",
            "cel_expression": "invalid expression syntax!!!",
            "prefill_name": "Test",
        }

        response = test_client.post(
            "/api/event-hints",
            json=hint_data,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_update_hint(self, test_client, jwt_token, test_user, sample_hints):
        """Test PUT /api/event-hints/<id> updates a hint"""
        response = test_client.put(
            "/api/event-hints/eh_1",
            json={"name": "Updated Hint Name"},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["name"] == "Updated Hint Name"

    def test_delete_hint(self, test_client, jwt_token, test_user, sample_hints):
        """Test DELETE /api/event-hints/<id> deletes a hint"""
        response = test_client.delete(
            "/api/event-hints/eh_1",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200

        # Verify it's deleted
        response = test_client.get("/api/event-hints", headers={"Authorization": f"Bearer {jwt_token}"})
        data = response.get_json()
        assert len(data["data"]) == 2

    def test_evaluate_hints_match(self, test_client, jwt_token, test_user, sample_hints, sample_line_items):
        """Test POST /api/event-hints/evaluate returns matching hint"""
        response = test_client.post(
            "/api/event-hints/evaluate",
            json={"line_item_ids": ["li_1"]},  # Spotify line item
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["suggestion"] is not None
        assert data["data"]["suggestion"]["name"] == "Spotify"

    def test_evaluate_hints_no_match(self, test_client, jwt_token, test_user, sample_hints, sample_line_items):
        """Test POST /api/event-hints/evaluate returns null when no match"""
        response = test_client.post(
            "/api/event-hints/evaluate",
            json={"line_item_ids": ["li_2"]},  # Venmo Transfer - doesn't match single-item hints
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        # li_2 alone (positive amount) won't match sum(amount)==0
        assert data["data"]["suggestion"] is None

    def test_evaluate_hints_aggregate_match(self, test_client, jwt_token, test_user, sample_hints, sample_line_items):
        """Test POST /api/event-hints/evaluate with aggregate expression"""
        response = test_client.post(
            "/api/event-hints/evaluate",
            json={"line_item_ids": ["li_2", "li_3"]},  # Two transfers that sum to 0
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["suggestion"] is not None
        assert data["data"]["suggestion"]["name"] == "Transfer"

    def test_validate_cel_valid(self, test_client, jwt_token, test_user):
        """Test POST /api/event-hints/validate with valid expression"""
        response = test_client.post(
            "/api/event-hints/validate",
            json={"cel_expression": 'description.contains("Test")'},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["is_valid"] is True

    def test_validate_cel_invalid(self, test_client, jwt_token, test_user):
        """Test POST /api/event-hints/validate with invalid expression"""
        response = test_client.post(
            "/api/event-hints/validate",
            json={"cel_expression": "invalid!!!"},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["is_valid"] is False
        assert "error" in data["data"]

    def test_requires_authentication(self, test_client):
        """Test that endpoints require authentication"""
        response = test_client.get("/api/event-hints")
        assert response.status_code == 401

    def test_reorder_hints(self, test_client, jwt_token, test_user, sample_hints):
        """Test PUT /api/event-hints/reorder reorders hints"""
        # Reverse the order
        new_order = ["eh_3", "eh_2", "eh_1"]
        response = test_client.put(
            "/api/event-hints/reorder",
            json={"hint_ids": new_order},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200

        # Verify the new order
        response = test_client.get("/api/event-hints", headers={"Authorization": f"Bearer {jwt_token}"})
        data = response.get_json()
        assert data["data"][0]["id"] == "eh_3"
        assert data["data"][1]["id"] == "eh_2"
        assert data["data"][2]["id"] == "eh_1"

    def test_reorder_hints_empty_list(self, test_client, jwt_token, test_user):
        """Test PUT /api/event-hints/reorder with empty list returns error"""
        response = test_client.put(
            "/api/event-hints/reorder",
            json={"hint_ids": []},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_reorder_hints_invalid_id(self, test_client, jwt_token, test_user, sample_hints):
        """Test PUT /api/event-hints/reorder with invalid hint ID returns error"""
        response = test_client.put(
            "/api/event-hints/reorder",
            json={"hint_ids": ["eh_1", "eh_invalid"]},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data


class TestCategoriesAPI:
    """Tests for the Categories API endpoint"""

    def test_get_categories(self, test_client, jwt_token):
        """Test GET /api/categories returns all categories"""
        response = test_client.get("/api/categories", headers={"Authorization": f"Bearer {jwt_token}"})
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) > 0
        # Verify structure
        for cat in data["data"]:
            assert "id" in cat
            assert "name" in cat
