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

    def test_contains_matches_substring_in_description(self):
        """Contains expression matches substring in description"""
        evaluator = CELEvaluator('description.contains("Spotify")')
        line_items = [{"description": "Spotify Premium Monthly", "amount": 9.99}]
        assert evaluator.evaluate(line_items) is True

    def test_contains_is_case_insensitive(self):
        """Contains matching ignores case differences"""
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

    def test_contains_returns_false_when_no_match(self):
        """Contains returns false when substring not found"""
        evaluator = CELEvaluator('description.contains("Netflix")')
        line_items = [{"description": "Spotify Premium", "amount": 9.99}]
        assert evaluator.evaluate(line_items) is False

    def test_amount_comparison_evaluates_correctly(self):
        """Amount comparisons evaluate greater/less than correctly"""
        evaluator = CELEvaluator("amount > 10")
        line_items = [{"description": "Test", "amount": 15.00}]
        assert evaluator.evaluate(line_items) is True

        line_items = [{"description": "Test", "amount": 5.00}]
        assert evaluator.evaluate(line_items) is False

    def test_and_conditions_require_both_to_match(self):
        """AND conditions require both expressions to be true"""
        evaluator = CELEvaluator('description.contains("Uber") && amount < 50')
        line_items = [{"description": "Uber Trip", "amount": 25.00}]
        assert evaluator.evaluate(line_items) is True

        line_items = [{"description": "Uber Trip", "amount": 75.00}]
        assert evaluator.evaluate(line_items) is False

    def test_any_matching_line_item_returns_true(self):
        """Expression returns true if any line item matches"""
        evaluator = CELEvaluator('description.contains("Spotify")')
        line_items = [
            {"description": "Netflix", "amount": 15.00},
            {"description": "Spotify Premium", "amount": 9.99},
        ]
        assert evaluator.evaluate(line_items) is True

    def test_empty_line_items_returns_false(self):
        """Empty line items list returns false"""
        evaluator = CELEvaluator('description.contains("Spotify")')
        assert evaluator.evaluate([]) is False

    def test_sum_aggregates_all_line_item_amounts(self):
        """Sum function aggregates amounts across all line items"""
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

    def test_sum_handles_floating_point_precision_with_multiple_items(self):
        """Sum correctly handles floating-point precision with 3+ items"""
        evaluator = CELEvaluator("sum(amount) == 0")
        # These values cause floating-point precision issues without rounding:
        # -16.67 + -16.66 + 33.33 = -3.55e-15 (not exactly 0)
        line_items = [
            {"description": "Split 1", "amount": -16.67},
            {"description": "Split 2", "amount": -16.66},
            {"description": "Total", "amount": 33.33},
        ]
        assert evaluator.evaluate(line_items) is True

    def test_count_returns_number_of_line_items(self):
        """Count function returns total number of line items"""
        evaluator = CELEvaluator("count() > 1")
        line_items = [
            {"description": "Item 1", "amount": 10.00},
            {"description": "Item 2", "amount": 20.00},
        ]
        assert evaluator.evaluate(line_items) is True

        line_items = [{"description": "Item 1", "amount": 10.00}]
        assert evaluator.evaluate(line_items) is False

    def test_all_match_requires_every_item_to_match(self):
        """All match requires every line item to satisfy condition"""
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

    def test_any_match_needs_only_one_item_to_match(self):
        """Any match returns true if at least one item matches"""
        evaluator = CELEvaluator('any_match(payment_method == "Venmo")')
        line_items = [
            {"description": "Item 1", "amount": 10.00, "payment_method": "Cash"},
            {"description": "Item 2", "amount": 20.00, "payment_method": "Venmo"},
        ]
        assert evaluator.evaluate(line_items) is True


class TestCELValidation:
    """Tests for CEL expression validation"""

    def test_simple_contains_expression_is_valid(self):
        """Simple contains expression passes validation"""
        is_valid, error = CELEvaluator.validate('description.contains("Spotify")')
        assert is_valid is True
        assert error is None

    def test_comparison_expression_is_valid(self):
        """Numeric comparison expression passes validation"""
        is_valid, error = CELEvaluator.validate("amount > 100")
        assert is_valid is True
        assert error is None

    def test_aggregate_expression_is_valid(self):
        """Aggregate sum expression passes validation"""
        is_valid, error = CELEvaluator.validate("sum(amount) == 0")
        assert is_valid is True
        assert error is None

    def test_empty_expression_is_invalid(self):
        """Empty expression fails validation"""
        is_valid, error = CELEvaluator.validate("")
        assert is_valid is False
        assert error is not None

    def test_malformed_syntax_is_invalid(self):
        """Malformed syntax fails validation"""
        is_valid, error = CELEvaluator.validate("description contains")
        assert is_valid is False
        assert error is not None

    def test_expression_exceeding_500_chars_is_rejected(self):
        """Expressions longer than 500 characters are rejected"""
        # Create an expression that exceeds the 500 character limit
        long_expression = 'description.contains("' + "a" * 500 + '")'
        is_valid, error = CELEvaluator.validate(long_expression)
        assert is_valid is False
        assert "too long" in error.lower()

    def test_expression_under_length_limit_is_accepted(self):
        """Expressions under 500 characters are accepted"""
        # Create an expression that is exactly at the limit (if valid syntax)
        expression = 'description.contains("test")'  # 28 chars, well under limit
        is_valid, error = CELEvaluator.validate(expression)
        assert is_valid is True
        assert error is None

    def test_nesting_exceeding_10_levels_is_rejected(self):
        """Expressions with more than 10 nesting levels are rejected"""
        # Create a deeply nested expression (11 levels of parentheses)
        nested_expression = "(" * 11 + "amount > 0" + ")" * 11
        is_valid, error = CELEvaluator.validate(nested_expression)
        assert is_valid is False
        assert "nested" in error.lower()

    def test_nesting_at_10_levels_is_accepted(self):
        """Expressions with exactly 10 nesting levels are accepted"""
        # Create an expression with exactly 10 levels of nesting
        nested_expression = "(" * 10 + "amount > 0" + ")" * 10
        is_valid, error = CELEvaluator.validate(nested_expression)
        assert is_valid is True
        assert error is None


class TestEvaluateHints:
    """Tests for the evaluate_hints function"""

    def test_first_matching_hint_is_returned(self):
        """When multiple hints match first one in order wins"""
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

    def test_inactive_hints_are_skipped(self):
        """Inactive hints are not evaluated"""
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

    def test_no_matching_hint_returns_none(self):
        """No matching hint returns None"""
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

    def test_empty_hints_returns_empty_list(self, test_client, jwt_token, test_user):
        """No hints returns empty list"""
        response = test_client.get("/api/event-hints", headers={"Authorization": f"Bearer {jwt_token}"})
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert data["data"] == []

    def test_hints_returns_all_user_hints(self, test_client, jwt_token, test_user, sample_hints):
        """All user hints are returned"""
        response = test_client.get("/api/event-hints", headers={"Authorization": f"Bearer {jwt_token}"})
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) == 3

    def test_new_hint_is_created_with_prefill_data(self, test_client, jwt_token, test_user, pg_session):
        """Creating hint stores name and prefill data"""
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

    def test_invalid_cel_expression_is_rejected(self, test_client, jwt_token, test_user):
        """Invalid CEL expression is rejected"""
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

    def test_hint_name_can_be_updated(self, test_client, jwt_token, test_user, sample_hints):
        """Hint name can be changed via update"""
        response = test_client.put(
            "/api/event-hints/eh_1",
            json={"name": "Updated Hint Name"},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["name"] == "Updated Hint Name"

    def test_hint_can_be_deleted(self, test_client, jwt_token, test_user, sample_hints):
        """Deleting hint removes it from list"""
        response = test_client.delete(
            "/api/event-hints/eh_1",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 204

        # Verify it's deleted
        response = test_client.get("/api/event-hints", headers={"Authorization": f"Bearer {jwt_token}"})
        data = response.get_json()
        assert len(data["data"]) == 2

    def test_evaluate_returns_matching_suggestion(self, test_client, jwt_token, test_user, sample_hints, sample_line_items):
        """Evaluate returns suggestion from matching hint"""
        response = test_client.post(
            "/api/event-hints/evaluate",
            json={"line_item_ids": ["li_1"]},  # Spotify line item
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["suggestion"] is not None
        assert data["data"]["suggestion"]["name"] == "Spotify"

    def test_evaluate_returns_null_when_no_match(self, test_client, jwt_token, test_user, sample_hints, sample_line_items):
        """Evaluate returns null when no hint matches"""
        response = test_client.post(
            "/api/event-hints/evaluate",
            json={"line_item_ids": ["li_2"]},  # Venmo Transfer - doesn't match single-item hints
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        # li_2 alone (positive amount) won't match sum(amount)==0
        assert data["data"]["suggestion"] is None

    def test_aggregate_matches_multiple_line_items(self, test_client, jwt_token, test_user, sample_hints, sample_line_items):
        """Aggregate expression evaluates across multiple line items"""
        response = test_client.post(
            "/api/event-hints/evaluate",
            json={"line_item_ids": ["li_2", "li_3"]},  # Two transfers that sum to 0
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["suggestion"] is not None
        assert data["data"]["suggestion"]["name"] == "Transfer"

    def test_validate_returns_true_for_valid_expression(self, test_client, jwt_token, test_user):
        """Validate returns is_valid true for valid CEL"""
        response = test_client.post(
            "/api/event-hints/validate",
            json={"cel_expression": 'description.contains("Test")'},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["is_valid"] is True

    def test_validate_returns_false_with_error_for_invalid_expression(self, test_client, jwt_token, test_user):
        """Validate returns is_valid false with error for invalid CEL"""
        response = test_client.post(
            "/api/event-hints/validate",
            json={"cel_expression": "invalid!!!"},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["is_valid"] is False
        assert "error" in data["data"]

    def test_endpoints_require_authentication(self, test_client):
        """Event hints endpoints require authentication"""
        response = test_client.get("/api/event-hints")
        assert response.status_code == 401


class TestCategoriesAPI:
    """Tests for the Categories API endpoint"""

    def test_categories_returns_all_with_id_and_name(self, test_client, jwt_token):
        """Categories returns all categories with id and name"""
        response = test_client.get("/api/categories", headers={"Authorization": f"Bearer {jwt_token}"})
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) > 0
        # Verify structure
        for cat in data["data"]:
            assert "id" in cat
            assert "name" in cat
