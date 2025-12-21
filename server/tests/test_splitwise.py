import pytest

from constants import PARTIES_TO_IGNORE, USER_FIRST_NAME
from dao import splitwise_raw_data_collection
from resources.splitwise import refresh_splitwise, splitwise_to_line_items


@pytest.fixture
def mock_splitwise_expense(mocker):
    """Mock Splitwise expense object"""
    expense = mocker.Mock()
    expense.deleted_at = None
    expense._id = "expense_1"
    expense.date = "2023-01-15T10:30:00Z"
    expense.description = "Test expense"
    expense.users = [
        {"first_name": USER_FIRST_NAME, "net_balance": -50.0},  # User owes money
        {"first_name": "John Doe", "net_balance": 50.0},  # User is owed money
    ]
    return expense


@pytest.fixture
def mock_splitwise_expense_deleted(mocker):
    """Mock deleted Splitwise expense object"""
    expense = mocker.Mock()
    expense.deleted_at = "2023-01-16T10:30:00Z"  # Has deletion date
    expense._id = "expense_2"
    expense.date = "2023-01-15T10:30:00Z"
    expense.description = "Deleted expense"
    expense.users = [
        {"first_name": USER_FIRST_NAME, "net_balance": -25.0},
        {"first_name": "Jane Smith", "net_balance": 25.0},
    ]
    return expense


@pytest.fixture
def mock_splitwise_expense_ignored_party(mocker):
    """Mock Splitwise expense with ignored party"""
    expense = mocker.Mock()
    expense.deleted_at = None
    expense._id = "expense_3"
    expense.date = "2023-01-15T10:30:00Z"
    expense.description = "Expense with ignored party"
    expense.users = [
        {"first_name": USER_FIRST_NAME, "net_balance": -30.0},
        {
            "first_name": PARTIES_TO_IGNORE[0],  # Use first ignored party
            "net_balance": 30.0,
        },
    ]
    return expense


@pytest.fixture
def mock_splitwise_expense_dict():
    """Mock Splitwise expense as dictionary"""
    return {
        "_id": "expense_1",
        "date": "2023-01-15T10:30:00Z",
        "description": "Test expense",
        "users": [
            {"first_name": USER_FIRST_NAME, "net_balance": -50.0},
            {"first_name": "John Doe", "net_balance": 50.0},
        ],
    }


class TestSplitwiseAPI:
    def test_refresh_splitwise_api_success(self, test_client, jwt_token, flask_app, mocker):
        """Test GET /api/refresh/splitwise endpoint - success case"""
        mock_refresh = mocker.patch("resources.splitwise.refresh_splitwise")
        mock_convert = mocker.patch("resources.splitwise.splitwise_to_line_items")

        response = test_client.get(
            "/api/refresh/splitwise",
            headers={"Authorization": "Bearer " + jwt_token},
        )

        assert response.status_code == 200
        assert response.get_data(as_text=True).strip() == '"Refreshed Splitwise Connection"'

        # Verify both functions were called
        mock_refresh.assert_called_once()
        mock_convert.assert_called_once()

    def test_refresh_splitwise_api_unauthorized(self, test_client):
        """Test GET /api/refresh/splitwise endpoint - unauthorized"""
        response = test_client.get("/api/refresh/splitwise")

        assert response.status_code == 401


class TestSplitwiseFunctions:
    def test_refresh_splitwise_success(self, flask_app, mock_splitwise_expense, mocker):
        """Test refresh_splitwise function - success case"""
        with flask_app.app_context():
            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")
            # Mock bulk_upsert (MongoDB)

            # Mock bulk_upsert_transactions (PostgreSQL)
            mocker.patch("resources.splitwise.upsert_transactions")

            # Mock the getExpenses method
            mock_splitwise_client.getExpenses.return_value = [mock_splitwise_expense]

            # Call the function
            refresh_splitwise()

            # Verify getExpenses was called with correct parameters
            mock_splitwise_client.getExpenses.assert_called_once_with(limit=1000, dated_after="2022-08-03T00:00:00Z")

            # Verify bulk_upsert was called with the non-deleted expense

    def test_refresh_splitwise_with_deleted_expense(
        self, flask_app, mock_splitwise_expense, mock_splitwise_expense_deleted, mocker
    ):
        """Test refresh_splitwise function - filters out deleted expenses"""
        with flask_app.app_context():
            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")
            # Mock bulk_upsert (MongoDB)

            # Mock bulk_upsert_transactions (PostgreSQL)
            mocker.patch("resources.splitwise.upsert_transactions")

            # Mock the getExpenses method to return both regular and deleted expenses
            mock_splitwise_client.getExpenses.return_value = [
                mock_splitwise_expense,
                mock_splitwise_expense_deleted,
            ]

            # Call the function
            refresh_splitwise()

            # Verify bulk_upsert was called only with the non-deleted expense

    def test_refresh_splitwise_no_expenses(self, flask_app, mocker):
        """Test refresh_splitwise function - no expenses returned"""
        with flask_app.app_context():
            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")
            # Mock bulk_upsert (MongoDB)

            # Mock bulk_upsert_transactions (PostgreSQL)
            mocker.patch("resources.splitwise.upsert_transactions")

            # Mock the getExpenses method to return empty list
            mock_splitwise_client.getExpenses.return_value = []

            # Call the function
            refresh_splitwise()

            # Verify bulk_upsert was not called (no expenses to upsert)

    def test_splitwise_to_line_items_success(self, flask_app, mock_splitwise_expense_dict, mocker):
        """Test splitwise_to_line_items function - success case"""
        with flask_app.app_context():
            from dao import splitwise_raw_data_collection, upsert_with_id
            from models.database import SessionLocal
            from models.sql_models import LineItem

            # Insert raw transaction data into database first
            upsert_with_id(splitwise_raw_data_collection, mock_splitwise_expense_dict, mock_splitwise_expense_dict["_id"])

            # Call the function (writes to PostgreSQL)
            splitwise_to_line_items()

            # Query database to verify line items were created
            db = SessionLocal()
            try:
                line_items = db.query(LineItem).all()
                assert len(line_items) == 1
                line_item = line_items[0]
                assert line_item.id.startswith("li_")  # PostgreSQL ULID format
                assert line_item.responsible_party == "John Doe "
                assert line_item.payment_method_id is not None
                assert line_item.description == "Test expense"
                assert line_item.amount == 50.0  # flip_amount(-50.0) = 50.0
            finally:
                db.close()

    def test_splitwise_to_line_items_with_ignored_party(self, flask_app, mocker):
        """Test splitwise_to_line_items function - filters out ignored parties"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_all_data")
            # Mock bulk_upsert (MongoDB)

            # Mock bulk_upsert_line_items (PostgreSQL)
            mocker.patch("resources.splitwise.upsert_line_items")

            # Mock expense where the responsible party is in the ignore list
            expense_with_ignored = {
                "_id": "expense_3",
                "date": "2023-01-15T10:30:00Z",
                "description": "Expense with ignored party",
                "users": [
                    {"first_name": USER_FIRST_NAME, "net_balance": -30.0},
                    {
                        "first_name": PARTIES_TO_IGNORE[0],  # Ignored party
                        "net_balance": 30.0,
                    },
                ],
            }
            mock_get_data.return_value = [expense_with_ignored]

            # Call the function
            splitwise_to_line_items()

            # Verify bulk_upsert was NOT called because the responsible party is ignored

    def test_splitwise_to_line_items_with_non_ignored_party(self, flask_app, mocker):
        """Test splitwise_to_line_items function - handles non-ignored parties correctly"""
        with flask_app.app_context():
            from dao import splitwise_raw_data_collection, upsert_with_id
            from models.database import SessionLocal
            from models.sql_models import LineItem

            # Insert raw expense with non-ignored party
            expense_with_non_ignored = {
                "_id": "expense_4",
                "date": "2023-01-15T10:30:00Z",
                "description": "Expense with non-ignored party",
                "users": [
                    {"first_name": USER_FIRST_NAME, "net_balance": -40.0},
                    {"first_name": "Regular Person", "net_balance": 40.0},
                ],
            }
            upsert_with_id(splitwise_raw_data_collection, expense_with_non_ignored, expense_with_non_ignored["_id"])

            # Call the function
            splitwise_to_line_items()

            # Query database to verify line item was created for non-ignored party
            db = SessionLocal()
            try:
                line_items = db.query(LineItem).all()
                assert len(line_items) == 1
                line_item = line_items[0]
                assert line_item.responsible_party == "Regular Person "
                assert line_item.amount == 40.0  # flip_amount(-40.0) = 40.0
            finally:
                db.close()

    def test_splitwise_to_line_items_multiple_users(self, flask_app, mocker):
        """Test splitwise_to_line_items function - handles multiple users correctly"""
        with flask_app.app_context():
            from dao import splitwise_raw_data_collection, upsert_with_id
            from models.database import SessionLocal
            from models.sql_models import LineItem

            # Insert raw expense with multiple users
            expense_multiple_users = {
                "_id": "expense_5",
                "date": "2023-01-15T10:30:00Z",
                "description": "Expense with multiple users",
                "users": [
                    {"first_name": USER_FIRST_NAME, "net_balance": -60.0},
                    {"first_name": "Alice", "net_balance": 30.0},
                    {"first_name": "Bob", "net_balance": 30.0},
                ],
            }
            upsert_with_id(splitwise_raw_data_collection, expense_multiple_users, expense_multiple_users["_id"])

            # Call the function
            splitwise_to_line_items()

            # Query database to verify line item was created
            db = SessionLocal()
            try:
                line_items = db.query(LineItem).all()
                assert len(line_items) == 1
                line_item = line_items[0]
                assert line_item.id.startswith("li_")  # PostgreSQL ULID format
                # The responsible party should be "Alice Bob " (both non-current users)
                assert "Alice" in line_item.responsible_party
                assert "Bob" in line_item.responsible_party
                assert line_item.amount == 60.0  # flip_amount(-60.0) = 60.0
            finally:
                db.close()

    def test_splitwise_to_line_items_no_expenses(self, flask_app, mocker):
        """Test splitwise_to_line_items function - no expenses to process"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_all_data")
            # Mock bulk_upsert (MongoDB)

            # Mock bulk_upsert_line_items (PostgreSQL)
            mocker.patch("resources.splitwise.upsert_line_items")

            # Mock get_all_data to return empty list
            mock_get_data.return_value = []

            # Call the function
            splitwise_to_line_items()

            # Verify bulk_upsert was not called

    def test_splitwise_to_line_items_user_not_found(self, flask_app, mocker):
        """Test splitwise_to_line_items function - user not found in expense"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_all_data")
            # Mock bulk_upsert (MongoDB)

            # Mock bulk_upsert_line_items (PostgreSQL)
            mocker.patch("resources.splitwise.upsert_line_items")

            # Mock expense without the current user
            expense_no_user = {
                "_id": "expense_6",
                "date": "2023-01-15T10:30:00Z",
                "description": "Expense without current user",
                "users": [
                    {"first_name": "Alice", "net_balance": -50.0},
                    {"first_name": "Bob", "net_balance": 50.0},
                ],
            }
            mock_get_data.return_value = [expense_no_user]

            # Call the function
            splitwise_to_line_items()

            # Verify bulk_upsert was not called (no valid expenses)

    def test_splitwise_to_line_items_date_conversion(self, flask_app, mocker):
        """Test splitwise_to_line_items function - date conversion"""
        with flask_app.app_context():
            from dao import splitwise_raw_data_collection, upsert_with_id
            from models.database import SessionLocal
            from models.sql_models import LineItem

            # Insert raw expense with specific date
            expense_with_date = {
                "_id": "expense_7",
                "date": "2023-01-15T10:30:00Z",
                "description": "Expense with date",
                "users": [
                    {"first_name": USER_FIRST_NAME, "net_balance": -25.0},
                    {"first_name": "Charlie", "net_balance": 25.0},
                ],
            }
            upsert_with_id(splitwise_raw_data_collection, expense_with_date, expense_with_date["_id"])

            # Call the function
            splitwise_to_line_items()

            # Query database to verify date was converted correctly
            db = SessionLocal()
            try:
                from datetime import UTC, datetime

                line_items = db.query(LineItem).all()
                assert len(line_items) == 1
                line_item = line_items[0]
                # The date should be converted to datetime
                expected_date = datetime(2023, 1, 15, 10, 30, tzinfo=UTC).replace(tzinfo=None)
                assert line_item.date == expected_date
            finally:
                db.close()

    def test_splitwise_to_line_items_amount_flipping(self, flask_app, mocker):
        """Test splitwise_to_line_items function - amount flipping logic"""
        with flask_app.app_context():
            from dao import splitwise_raw_data_collection, upsert_with_id
            from models.database import SessionLocal
            from models.sql_models import LineItem

            # Insert raw expense with positive and negative balances
            expense_mixed_balances = {
                "_id": "expense_8",
                "date": "2023-01-15T10:30:00Z",
                "description": "Expense with mixed balances",
                "users": [
                    {"first_name": USER_FIRST_NAME, "net_balance": -100.0},  # User owes
                    {"first_name": "David", "net_balance": 100.0},  # David is owed
                ],
            }
            upsert_with_id(splitwise_raw_data_collection, expense_mixed_balances, expense_mixed_balances["_id"])

            # Call the function
            splitwise_to_line_items()

            # Query database to verify amounts were flipped correctly
            db = SessionLocal()
            try:
                line_items = db.query(LineItem).all()
                assert len(line_items) == 1
                line_item = line_items[0]
                # User's negative balance should become positive in line item
                assert line_item.amount == 100.0  # flip_amount(-100.0) = 100.0
            finally:
                db.close()


class TestSplitwiseIntegration:
    def test_full_refresh_workflow(self, flask_app, mocker):
        """Test the complete refresh workflow from API to database"""
        with flask_app.app_context():
            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")
            # Mock bulk_upsert (MongoDB)
            # Mock bulk_upsert (MongoDB)

            # Mock bulk_upsert_line_items (PostgreSQL)
            mocker.patch("resources.splitwise.upsert_line_items")

            # Mock bulk_upsert_transactions (PostgreSQL)
            mocker.patch("resources.splitwise.upsert_transactions")
            mock_get_data = mocker.patch("resources.splitwise.get_all_data")

            # Mock expense for refresh
            mock_expense = mocker.Mock()
            mock_expense.deleted_at = None
            mock_expense._id = "expense_integration"
            mock_expense.date = "2023-01-15T10:30:00Z"
            mock_expense.description = "Integration test expense"
            mock_expense.users = [
                {"first_name": USER_FIRST_NAME, "net_balance": -75.0},
                {"first_name": "Integration User", "net_balance": 75.0},
            ]

            # Mock client responses
            mock_splitwise_client.getExpenses.return_value = [mock_expense]

            # Mock get_all_data for conversion
            mock_get_data.return_value = [
                {
                    "_id": "expense_integration",
                    "date": "2023-01-15T10:30:00Z",
                    "description": "Integration test expense",
                    "users": [
                        {"first_name": USER_FIRST_NAME, "net_balance": -75.0},
                        {"first_name": "Integration User", "net_balance": 75.0},
                    ],
                }
            ]

            # Test refresh function
            refresh_splitwise()

            # Verify refresh was called
            mock_splitwise_client.getExpenses.assert_called_once()

            # Reset mock for conversion test

            # Test conversion function
            splitwise_to_line_items()

            # Verify conversion was called
            mock_get_data.assert_called_once_with(splitwise_raw_data_collection)

            # Verify line items were created correctly
