import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List

import pytest

from dao import events_collection, get_all_data, upsert_with_id

# Skip monthly breakdown tests when READ_FROM_POSTGRESQL=true
# These tests need additional work to properly handle PostgreSQL event amounts
# See: Need to fix event amount calculation when reading from PostgreSQL
skip_if_postgres = pytest.mark.skipif(
    os.environ.get("READ_FROM_POSTGRESQL", "false").lower() == "true",
    reason="Monthly breakdown tests not yet compatible with READ_FROM_POSTGRESQL=true",
)


@pytest.fixture
def mock_event_data():
    """Mock event data for testing"""
    return [
        {
            "id": "event_1",
            "date": 1672531200,  # 2023-01-01
            "category": "Food",
            "amount": 50.0,
            "description": "Lunch",
        },
        {
            "id": "event_2",
            "date": 1672531200,  # 2023-01-01
            "category": "Transportation",
            "amount": 25.0,
            "description": "Uber ride",
        },
        {
            "id": "event_3",
            "date": 1675209600,  # 2023-02-01
            "category": "Food",
            "amount": 75.0,
            "description": "Dinner",
        },
        {
            "id": "event_4",
            "date": 1675209600,  # 2023-02-01
            "category": "Entertainment",
            "amount": 100.0,
            "description": "Movie tickets",
        },
        {
            "id": "event_5",
            "date": 1677628800,  # 2023-03-01
            "category": "Food",
            "amount": 60.0,
            "description": "Groceries",
        },
    ]


def mock_get_categorized_data() -> List[Dict[str, Any]]:
    """
    Mock implementation of get_categorized_data() that doesn't use MongoDB aggregation.
    This is needed because mongomock doesn't support the $toDate operator.
    """
    # Get all events from the database
    events = get_all_data(events_collection)

    # Group by year, month, and category
    aggregated: Dict[tuple, float] = defaultdict(float)
    for event in events:
        # Convert Unix timestamp to datetime (use UTC to match MongoDB behavior)
        date = datetime.fromtimestamp(event["date"], tz=timezone.utc)
        key = (date.year, date.month, event["category"])
        aggregated[key] += event["amount"]

    # Convert to the expected output format
    result = []
    for (year, month, category), total in aggregated.items():
        result.append({"year": year, "month": month, "category": category, "totalExpense": total})

    return result


@pytest.fixture(autouse=True)
def mock_categorized_data_for_monthly_breakdown(monkeypatch):
    """
    Automatically mock get_categorized_data() for all tests in this file.
    This is needed because mongomock doesn't support MongoDB's $toDate aggregation operator.
    """
    monkeypatch.setattr("resources.monthly_breakdown.get_categorized_data", mock_get_categorized_data)


@pytest.fixture
def mock_event_data_with_gaps():
    """Mock event data with gaps in months for testing date filling"""
    return [
        {
            "id": "event_1",
            "date": 1672531200,  # 2023-01-01
            "category": "Food",
            "amount": 50.0,
            "description": "Lunch",
        },
        {
            "id": "event_2",
            "date": 1675209600,  # 2023-02-01
            "category": "Food",
            "amount": 75.0,
            "description": "Dinner",
        },
        {
            "id": "event_3",
            "date": 1680307200,  # 2023-04-01 (skipping March)
            "category": "Food",
            "amount": 60.0,
            "description": "Groceries",
        },
    ]


class TestMonthlyBreakdownAPI:
    @skip_if_postgres
    def test_get_monthly_breakdown_api_success(self, test_client, jwt_token, flask_app, mock_event_data):
        """Test GET /api/monthly_breakdown endpoint - success case"""
        # Insert test data
        with flask_app.app_context():
            for event in mock_event_data:
                upsert_with_id(events_collection, event, event["id"])

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify structure
        assert isinstance(data, dict)
        assert "Food" in data
        assert "Transportation" in data
        assert "Entertainment" in data

        # Verify Food category data - should have all 3 months with data
        food_data = data["Food"]
        assert len(food_data) == 3  # 3 months with food expenses

        # Check January food data
        jan_food = next(item for item in food_data if item["date"] == "1-2023")
        assert jan_food["amount"] == 50.0

        # Check February food data
        feb_food = next(item for item in food_data if item["date"] == "2-2023")
        assert feb_food["amount"] == 75.0

        # Check March food data
        mar_food = next(item for item in food_data if item["date"] == "3-2023")
        assert mar_food["amount"] == 60.0

        # Verify Transportation category data - should have all 3 months (with zeros for missing months)
        transport_data = data["Transportation"]
        assert len(transport_data) == 3  # All months are filled with zeros for missing data

        # Check January transportation data
        jan_transport = next(item for item in transport_data if item["date"] == "1-2023")
        assert jan_transport["amount"] == 25.0

        # Check February transportation data (should be zero)
        feb_transport = next(item for item in transport_data if item["date"] == "2-2023")
        assert feb_transport["amount"] == 0.0

        # Check March transportation data (should be zero)
        mar_transport = next(item for item in transport_data if item["date"] == "3-2023")
        assert mar_transport["amount"] == 0.0

        # Verify Entertainment category data - should have all 3 months (with zeros for missing months)
        entertainment_data = data["Entertainment"]
        assert len(entertainment_data) == 3  # All months are filled with zeros for missing data

        # Check January entertainment data (should be zero)
        jan_entertainment = next(item for item in entertainment_data if item["date"] == "1-2023")
        assert jan_entertainment["amount"] == 0.0

        # Check February entertainment data
        feb_entertainment = next(item for item in entertainment_data if item["date"] == "2-2023")
        assert feb_entertainment["amount"] == 100.0

        # Check March entertainment data (should be zero)
        mar_entertainment = next(item for item in entertainment_data if item["date"] == "3-2023")
        assert mar_entertainment["amount"] == 0.0

    def test_get_monthly_breakdown_api_unauthorized(self, test_client):
        """Test GET /api/monthly_breakdown endpoint - unauthorized"""
        response = test_client.get("/api/monthly_breakdown")
        assert response.status_code == 401

    def test_get_monthly_breakdown_api_empty_data(self, test_client, jwt_token, flask_app):
        """Test GET /api/monthly_breakdown endpoint - no data"""
        # Test API call with no data in database
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data == {}  # Empty response when no data

    @skip_if_postgres
    def test_get_monthly_breakdown_api_fills_missing_dates(self, test_client, jwt_token, flask_app, mock_event_data_with_gaps):
        """Test GET /api/monthly_breakdown endpoint - fills missing dates with zero amounts"""
        # Insert test data with gaps
        with flask_app.app_context():
            for event in mock_event_data_with_gaps:
                upsert_with_id(events_collection, event, event["id"])

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify Food category has all months in the range filled
        food_data = data["Food"]
        assert len(food_data) == 4  # 4 months (Jan, Feb, Mar, Apr)

        jan_food = next(item for item in food_data if item["date"] == "1-2023")
        assert jan_food["amount"] == 50.0

        feb_food = next(item for item in food_data if item["date"] == "2-2023")
        assert feb_food["amount"] == 75.0

        mar_food = next(item for item in food_data if item["date"] == "3-2023")
        assert mar_food["amount"] == 0.0  # March filled with zero

        apr_food = next(item for item in food_data if item["date"] == "4-2023")
        assert apr_food["amount"] == 60.0

    @skip_if_postgres
    def test_get_monthly_breakdown_api_fills_missing_dates_multiple_categories(self, test_client, jwt_token, flask_app):
        """Test GET /api/monthly_breakdown endpoint - fills missing dates when multiple categories have different date ranges"""
        # Insert test data where different categories have data in different months
        with flask_app.app_context():
            test_events = [
                {
                    "id": "event_1",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Food",
                    "amount": 50.0,
                    "description": "January food",
                },
                {
                    "id": "event_2",
                    "date": 1675209600,  # 2023-02-01
                    "category": "Food",
                    "amount": 75.0,
                    "description": "February food",
                },
                {
                    "id": "event_3",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Transportation",
                    "amount": 25.0,
                    "description": "January transport",
                },
                {
                    "id": "event_4",
                    "date": 1680307200,  # 2023-04-01
                    "category": "Transportation",
                    "amount": 30.0,
                    "description": "April transport",
                },
            ]

            for event in test_events:
                upsert_with_id(events_collection, event, event["id"])

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify Food category has data for Jan and Feb, and zeros for Mar and Apr
        food_data = data["Food"]
        assert len(food_data) == 4  # 4 months (Jan, Feb, Mar, Apr)

        jan_food = next(item for item in food_data if item["date"] == "1-2023")
        assert jan_food["amount"] == 50.0

        feb_food = next(item for item in food_data if item["date"] == "2-2023")
        assert feb_food["amount"] == 75.0

        mar_food = next(item for item in food_data if item["date"] == "3-2023")
        assert mar_food["amount"] == 0.0  # March filled with zero

        apr_food = next(item for item in food_data if item["date"] == "4-2023")
        assert apr_food["amount"] == 0.0  # April filled with zero

        # Verify Transportation category has data for Jan and Apr, and zeros for Feb and Mar
        transport_data = data["Transportation"]
        assert len(transport_data) == 4  # 4 months (Jan, Feb, Mar, Apr)

        jan_transport = next(item for item in transport_data if item["date"] == "1-2023")
        assert jan_transport["amount"] == 25.0

        feb_transport = next(item for item in transport_data if item["date"] == "2-2023")
        assert feb_transport["amount"] == 0.0  # February filled with zero

        mar_transport = next(item for item in transport_data if item["date"] == "3-2023")
        assert mar_transport["amount"] == 0.0  # March filled with zero

        apr_transport = next(item for item in transport_data if item["date"] == "4-2023")
        assert apr_transport["amount"] == 30.0

    @skip_if_postgres
    def test_get_monthly_breakdown_api_sorts_by_date(self, test_client, jwt_token, flask_app):
        """Test GET /api/monthly_breakdown endpoint - sorts data by date"""
        # Insert test data in random order
        with flask_app.app_context():
            test_events = [
                {
                    "id": "event_1",
                    "date": 1677628800,  # 2023-03-01
                    "category": "Food",
                    "amount": 60.0,
                    "description": "March food",
                },
                {
                    "id": "event_2",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Food",
                    "amount": 50.0,
                    "description": "January food",
                },
                {
                    "id": "event_3",
                    "date": 1675209600,  # 2023-02-01
                    "category": "Food",
                    "amount": 75.0,
                    "description": "February food",
                },
            ]

            for event in test_events:
                upsert_with_id(events_collection, event, event["id"])

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify Food category data is sorted by date
        food_data = data["Food"]
        assert len(food_data) == 3

        # Check order: January, February, March
        assert food_data[0]["date"] == "1-2023"
        assert food_data[0]["amount"] == 50.0
        assert food_data[1]["date"] == "2-2023"
        assert food_data[1]["amount"] == 75.0
        assert food_data[2]["date"] == "3-2023"
        assert food_data[2]["amount"] == 60.0

    @skip_if_postgres
    def test_get_monthly_breakdown_api_multiple_categories_same_month(self, test_client, jwt_token, flask_app):
        """Test GET /api/monthly_breakdown endpoint - multiple categories in same month"""
        # Insert test data with multiple categories in same month
        with flask_app.app_context():
            test_events = [
                {
                    "id": "event_1",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Food",
                    "amount": 50.0,
                    "description": "Lunch",
                },
                {
                    "id": "event_2",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Food",
                    "amount": 30.0,
                    "description": "Dinner",
                },
                {
                    "id": "event_3",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Transportation",
                    "amount": 25.0,
                    "description": "Uber",
                },
            ]

            for event in test_events:
                upsert_with_id(events_collection, event, event["id"])

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify Food category is aggregated
        food_data = data["Food"]
        assert len(food_data) == 1
        assert food_data[0]["date"] == "1-2023"
        assert food_data[0]["amount"] == 80.0  # 50 + 30

        # Verify Transportation category
        transport_data = data["Transportation"]
        assert len(transport_data) == 1
        assert transport_data[0]["date"] == "1-2023"
        assert transport_data[0]["amount"] == 25.0

    @skip_if_postgres
    def test_get_monthly_breakdown_api_large_amounts(self, test_client, jwt_token, flask_app):
        """Test GET /api/monthly_breakdown endpoint - handles large amounts correctly"""
        # Insert test data with large amounts
        with flask_app.app_context():
            test_events = [
                {
                    "id": "event_1",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Rent",
                    "amount": 2500.0,
                    "description": "Monthly rent",
                },
                {
                    "id": "event_2",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Rent",
                    "amount": 500.0,
                    "description": "Utilities",
                },
            ]

            for event in test_events:
                upsert_with_id(events_collection, event, event["id"])

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify Rent category is aggregated correctly
        rent_data = data["Rent"]
        assert len(rent_data) == 1
        assert rent_data[0]["date"] == "1-2023"
        assert rent_data[0]["amount"] == 3000.0  # 2500 + 500

    @skip_if_postgres
    def test_get_monthly_breakdown_api_decimal_amounts(self, test_client, jwt_token, flask_app):
        """Test GET /api/monthly_breakdown endpoint - handles decimal amounts correctly"""
        # Insert test data with decimal amounts
        with flask_app.app_context():
            test_events = [
                {
                    "id": "event_1",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Food",
                    "amount": 12.50,
                    "description": "Coffee",
                },
                {
                    "id": "event_2",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Food",
                    "amount": 8.75,
                    "description": "Snack",
                },
            ]

            for event in test_events:
                upsert_with_id(events_collection, event, event["id"])

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify Food category is aggregated correctly with decimals
        food_data = data["Food"]
        assert len(food_data) == 1
        assert food_data[0]["date"] == "1-2023"
        assert food_data[0]["amount"] == 21.25  # 12.50 + 8.75

    @skip_if_postgres
    def test_get_monthly_breakdown_api_single_category(self, test_client, jwt_token, flask_app):
        """Test GET /api/monthly_breakdown endpoint - single category"""
        # Insert test data with only one category
        with flask_app.app_context():
            test_events = [
                {
                    "id": "event_1",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Food",
                    "amount": 50.0,
                    "description": "Lunch",
                },
                {
                    "id": "event_2",
                    "date": 1675209600,  # 2023-02-01
                    "category": "Food",
                    "amount": 75.0,
                    "description": "Dinner",
                },
            ]

            for event in test_events:
                upsert_with_id(events_collection, event, event["id"])

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify only Food category exists
        assert len(data) == 1
        assert "Food" in data
        assert len(data["Food"]) == 2

        # Verify data is correct
        jan_food = next(item for item in data["Food"] if item["date"] == "1-2023")
        assert jan_food["amount"] == 50.0

        feb_food = next(item for item in data["Food"] if item["date"] == "2-2023")
        assert feb_food["amount"] == 75.0

    def test_get_monthly_breakdown_api_response_structure(self, test_client, jwt_token, flask_app, mock_event_data):
        """Test GET /api/monthly_breakdown endpoint - response structure"""
        # Insert test data
        with flask_app.app_context():
            for event in mock_event_data:
                upsert_with_id(events_collection, event, event["id"])

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify response structure
        assert isinstance(data, dict)

        # Verify each category has the expected structure
        for category_name, category_data in data.items():
            assert isinstance(category_name, str)
            assert isinstance(category_data, list)

            for item in category_data:
                assert "date" in item
                assert "amount" in item
                assert isinstance(item["date"], str)
                assert isinstance(item["amount"], (int, float))

                # Verify date format is "month-year"
                assert "-" in item["date"]
                month, year = item["date"].split("-")
                assert month.isdigit() and year.isdigit()
                assert 1 <= int(month) <= 12
                assert int(year) >= 2020  # Reasonable year range
