from typing import Any, Dict

import pytest

from tests.test_helpers import setup_test_event, setup_test_line_item


def create_event_with_line_item(pg_session, event_data: Dict[str, Any]) -> None:
    """
    Create a PostgreSQL event with a line item matching the amount.
    Converts simple event data to PostgreSQL structure with proper relationships.
    """
    # Create line item with the event's amount
    line_item_data = {
        "id": f"li_{event_data['id']}",
        "date": event_data["date"],
        "payment_method": "Cash",  # Default for tests
        "description": event_data.get("description", ""),
        "responsible_party": "Test User",
        "amount": event_data["amount"],
        "notes": None,
    }

    pg_line_item = setup_test_line_item(pg_session, line_item_data)

    # Create event and associate the line item
    setup_test_event(pg_session, event_data, line_items=[pg_line_item])

    pg_session.flush()


@pytest.fixture
def mock_event_data():
    """Mock event data for testing"""
    return [
        {
            "id": "event_1",
            "date": 1672531200,  # 2023-01-01
            "category": "Dining",
            "amount": 50.0,
            "description": "Lunch",
        },
        {
            "id": "event_2",
            "date": 1672531200,  # 2023-01-01
            "category": "Transit",
            "amount": 25.0,
            "description": "Uber ride",
        },
        {
            "id": "event_3",
            "date": 1675209600,  # 2023-02-01
            "category": "Dining",
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
            "category": "Dining",
            "amount": 60.0,
            "description": "Groceries",
        },
    ]


@pytest.fixture
def mock_event_data_with_gaps():
    """Mock event data with gaps in months for testing date filling"""
    return [
        {
            "id": "event_1",
            "date": 1672531200,  # 2023-01-01
            "category": "Dining",
            "amount": 50.0,
            "description": "Lunch",
        },
        {
            "id": "event_2",
            "date": 1675209600,  # 2023-02-01
            "category": "Dining",
            "amount": 75.0,
            "description": "Dinner",
        },
        {
            "id": "event_3",
            "date": 1680307200,  # 2023-04-01 (skipping March)
            "category": "Dining",
            "amount": 60.0,
            "description": "Groceries",
        },
    ]


class TestMonthlyBreakdownAPI:
    def test_get_monthly_breakdown_api_success(self, test_client, jwt_token, flask_app, mock_event_data, pg_session):
        """Test GET /api/monthly_breakdown endpoint - success case"""
        # Insert test data
        with flask_app.app_context():
            for event in mock_event_data:
                create_event_with_line_item(pg_session, event)
            pg_session.commit()

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify structure
        assert isinstance(data, dict)
        assert "Dining" in data
        assert "Transit" in data
        assert "Entertainment" in data

        # Verify Dining category data - should have all 3 months with data
        dining_data = data["Dining"]
        assert len(dining_data) == 3  # 3 months with dining expenses

        # Check January dining data
        jan_dining = next(item for item in dining_data if item["date"] == "1-2023")
        assert jan_dining["amount"] == 50.0

        # Check February dining data
        feb_dining = next(item for item in dining_data if item["date"] == "2-2023")
        assert feb_dining["amount"] == 75.0

        # Check March dining data
        mar_dining = next(item for item in dining_data if item["date"] == "3-2023")
        assert mar_dining["amount"] == 60.0

        # Verify Transit category data - should have all 3 months (with zeros for missing months)
        transit_data = data["Transit"]
        assert len(transit_data) == 3  # All months are filled with zeros for missing data

        # Check January transit data
        jan_transit = next(item for item in transit_data if item["date"] == "1-2023")
        assert jan_transit["amount"] == 25.0

        # Check February transit data (should be zero)
        feb_transit = next(item for item in transit_data if item["date"] == "2-2023")
        assert feb_transit["amount"] == 0.0

        # Check March transit data (should be zero)
        mar_transit = next(item for item in transit_data if item["date"] == "3-2023")
        assert mar_transit["amount"] == 0.0

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

    def test_get_monthly_breakdown_api_fills_missing_dates(
        self, test_client, jwt_token, flask_app, mock_event_data_with_gaps, pg_session
    ):
        """Test GET /api/monthly_breakdown endpoint - fills missing dates with zero amounts"""
        # Insert test data with gaps
        with flask_app.app_context():
            for event in mock_event_data_with_gaps:
                create_event_with_line_item(pg_session, event)
            pg_session.commit()

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify Dining category has all months in the range filled
        dining_data = data["Dining"]
        assert len(dining_data) == 4  # 4 months (Jan, Feb, Mar, Apr)

        jan_dining = next(item for item in dining_data if item["date"] == "1-2023")
        assert jan_dining["amount"] == 50.0

        feb_dining = next(item for item in dining_data if item["date"] == "2-2023")
        assert feb_dining["amount"] == 75.0

        mar_dining = next(item for item in dining_data if item["date"] == "3-2023")
        assert mar_dining["amount"] == 0.0  # March filled with zero

        apr_dining = next(item for item in dining_data if item["date"] == "4-2023")
        assert apr_dining["amount"] == 60.0

    def test_get_monthly_breakdown_api_fills_missing_dates_multiple_categories(
        self, test_client, jwt_token, flask_app, pg_session
    ):
        """
        Test GET /api/monthly_breakdown endpoint
        - fills missing dates when multiple categories have different date ranges
        """
        # Insert test data where different categories have data in different months
        with flask_app.app_context():
            test_events = [
                {
                    "id": "event_1",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Dining",
                    "amount": 50.0,
                    "description": "January food",
                },
                {
                    "id": "event_2",
                    "date": 1675209600,  # 2023-02-01
                    "category": "Dining",
                    "amount": 75.0,
                    "description": "February food",
                },
                {
                    "id": "event_3",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Transit",
                    "amount": 25.0,
                    "description": "January transport",
                },
                {
                    "id": "event_4",
                    "date": 1680307200,  # 2023-04-01
                    "category": "Transit",
                    "amount": 30.0,
                    "description": "April transport",
                },
            ]

            for event in test_events:
                create_event_with_line_item(pg_session, event)
            pg_session.commit()

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify Dining category has data for Jan and Feb, and zeros for Mar and Apr
        dining_data = data["Dining"]
        assert len(dining_data) == 4  # 4 months (Jan, Feb, Mar, Apr)

        jan_dining = next(item for item in dining_data if item["date"] == "1-2023")
        assert jan_dining["amount"] == 50.0

        feb_dining = next(item for item in dining_data if item["date"] == "2-2023")
        assert feb_dining["amount"] == 75.0

        mar_dining = next(item for item in dining_data if item["date"] == "3-2023")
        assert mar_dining["amount"] == 0.0  # March filled with zero

        apr_dining = next(item for item in dining_data if item["date"] == "4-2023")
        assert apr_dining["amount"] == 0.0  # April filled with zero

        # Verify Transit category has data for Jan and Apr, and zeros for Feb and Mar
        transit_data = data["Transit"]
        assert len(transit_data) == 4  # 4 months (Jan, Feb, Mar, Apr)

        jan_transit = next(item for item in transit_data if item["date"] == "1-2023")
        assert jan_transit["amount"] == 25.0

        feb_transit = next(item for item in transit_data if item["date"] == "2-2023")
        assert feb_transit["amount"] == 0.0  # February filled with zero

        mar_transit = next(item for item in transit_data if item["date"] == "3-2023")
        assert mar_transit["amount"] == 0.0  # March filled with zero

        apr_transit = next(item for item in transit_data if item["date"] == "4-2023")
        assert apr_transit["amount"] == 30.0

    def test_get_monthly_breakdown_api_sorts_by_date(self, test_client, jwt_token, flask_app, pg_session):
        """Test GET /api/monthly_breakdown endpoint - sorts data by date"""
        # Insert test data in random order
        with flask_app.app_context():
            test_events = [
                {
                    "id": "event_1",
                    "date": 1677628800,  # 2023-03-01
                    "category": "Dining",
                    "amount": 60.0,
                    "description": "March food",
                },
                {
                    "id": "event_2",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Dining",
                    "amount": 50.0,
                    "description": "January food",
                },
                {
                    "id": "event_3",
                    "date": 1675209600,  # 2023-02-01
                    "category": "Dining",
                    "amount": 75.0,
                    "description": "February food",
                },
            ]

            for event in test_events:
                create_event_with_line_item(pg_session, event)
            pg_session.commit()

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify Food category data is sorted by date
        dining_data = data["Dining"]
        assert len(dining_data) == 3

        # Check order: January, February, March
        assert dining_data[0]["date"] == "1-2023"
        assert dining_data[0]["amount"] == 50.0
        assert dining_data[1]["date"] == "2-2023"
        assert dining_data[1]["amount"] == 75.0
        assert dining_data[2]["date"] == "3-2023"
        assert dining_data[2]["amount"] == 60.0

    def test_get_monthly_breakdown_api_multiple_categories_same_month(self, test_client, jwt_token, flask_app, pg_session):
        """Test GET /api/monthly_breakdown endpoint - multiple categories in same month"""
        # Insert test data with multiple categories in same month
        with flask_app.app_context():
            test_events = [
                {
                    "id": "event_1",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Dining",
                    "amount": 50.0,
                    "description": "Lunch",
                },
                {
                    "id": "event_2",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Dining",
                    "amount": 30.0,
                    "description": "Dinner",
                },
                {
                    "id": "event_3",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Transit",
                    "amount": 25.0,
                    "description": "Uber",
                },
            ]

            for event in test_events:
                create_event_with_line_item(pg_session, event)
            pg_session.commit()

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify Dining category is aggregated
        dining_data = data["Dining"]
        assert len(dining_data) == 1
        assert dining_data[0]["date"] == "1-2023"
        assert dining_data[0]["amount"] == 80.0  # 50 + 30

        # Verify Transit category
        transit_data = data["Transit"]
        assert len(transit_data) == 1
        assert transit_data[0]["date"] == "1-2023"
        assert transit_data[0]["amount"] == 25.0

    def test_get_monthly_breakdown_api_large_amounts(self, test_client, jwt_token, flask_app, pg_session):
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
                create_event_with_line_item(pg_session, event)
            pg_session.commit()

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

    def test_get_monthly_breakdown_api_decimal_amounts(self, test_client, jwt_token, flask_app, pg_session):
        """Test GET /api/monthly_breakdown endpoint - handles decimal amounts correctly"""
        # Insert test data with decimal amounts
        with flask_app.app_context():
            test_events = [
                {
                    "id": "event_1",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Dining",
                    "amount": 12.50,
                    "description": "Coffee",
                },
                {
                    "id": "event_2",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Dining",
                    "amount": 8.75,
                    "description": "Snack",
                },
            ]

            for event in test_events:
                create_event_with_line_item(pg_session, event)
            pg_session.commit()

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify Food category is aggregated correctly with decimals
        dining_data = data["Dining"]
        assert len(dining_data) == 1
        assert dining_data[0]["date"] == "1-2023"
        assert dining_data[0]["amount"] == 21.25  # 12.50 + 8.75

    def test_get_monthly_breakdown_api_single_category(self, test_client, jwt_token, flask_app, pg_session):
        """Test GET /api/monthly_breakdown endpoint - single category"""
        # Insert test data with only one category
        with flask_app.app_context():
            test_events = [
                {
                    "id": "event_1",
                    "date": 1672531200,  # 2023-01-01
                    "category": "Dining",
                    "amount": 50.0,
                    "description": "Lunch",
                },
                {
                    "id": "event_2",
                    "date": 1675209600,  # 2023-02-01
                    "category": "Dining",
                    "amount": 75.0,
                    "description": "Dinner",
                },
            ]

            for event in test_events:
                create_event_with_line_item(pg_session, event)
            pg_session.commit()

        # Test API call
        response = test_client.get(
            "/api/monthly_breakdown",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify only Dining category exists
        assert len(data) == 1
        assert "Dining" in data
        assert len(data["Dining"]) == 2

        # Verify data is correct
        jan_dining = next(item for item in data["Dining"] if item["date"] == "1-2023")
        assert jan_dining["amount"] == 50.0

        feb_dining = next(item for item in data["Dining"] if item["date"] == "2-2023")
        assert feb_dining["amount"] == 75.0

    def test_get_monthly_breakdown_api_response_structure(
        self, test_client, jwt_token, flask_app, mock_event_data, pg_session
    ):
        """Test GET /api/monthly_breakdown endpoint - response structure"""
        # Insert test data
        with flask_app.app_context():
            for event in mock_event_data:
                create_event_with_line_item(pg_session, event)
            pg_session.commit()

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
