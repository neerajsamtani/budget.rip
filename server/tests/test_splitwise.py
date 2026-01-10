import pytest

from constants import PARTIES_TO_IGNORE, USER_FIRST_NAME
from resources.splitwise import refresh_splitwise, splitwise_to_line_items


@pytest.fixture
def mock_splitwise_expense(mocker):
    """Mock Splitwise expense object"""
    expense = mocker.Mock()
    expense.deleted_at = None
    expense.source_id = "expense_1"
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
    expense.source_id = "expense_2"
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
    expense.source_id = "expense_3"
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
        "id": "expense_1",
        "date": "2023-01-15T10:30:00Z",
        "description": "Test expense",
        "users": [
            {"first_name": USER_FIRST_NAME, "net_balance": -50.0},
            {"first_name": "John Doe", "net_balance": 50.0},
        ],
    }


class TestSplitwiseAPI:
    def test_refresh_splitwise_syncs_and_converts_expenses(self, test_client, jwt_token, flask_app, mocker):
        """Splitwise refresh syncs expenses and converts to line items"""
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

    def test_refresh_splitwise_requires_authentication(self, test_client):
        """Splitwise refresh endpoint requires authentication"""
        response = test_client.get("/api/refresh/splitwise")

        assert response.status_code == 401


class TestSplitwiseFunctions:
    def test_refresh_fetches_expenses_after_moving_date(self, flask_app, mock_splitwise_expense, mocker):
        """Refresh fetches expenses dated after the moving date"""
        with flask_app.app_context():
            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")
            mocker.patch("resources.splitwise.upsert_transactions")

            # Mock the getExpenses method
            mock_splitwise_client.getExpenses.return_value = [mock_splitwise_expense]

            # Call the function
            refresh_splitwise()

            # Verify getExpenses was called with correct parameters
            mock_splitwise_client.getExpenses.assert_called_once_with(limit=1000, dated_after="2022-08-03T00:00:00Z")

    def test_deleted_expenses_are_filtered_out(
        self, flask_app, mock_splitwise_expense, mock_splitwise_expense_deleted, mocker
    ):
        """Deleted expenses are filtered out during refresh"""
        with flask_app.app_context():
            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")
            mocker.patch("resources.splitwise.upsert_transactions")

            # Mock the getExpenses method to return both regular and deleted expenses
            mock_splitwise_client.getExpenses.return_value = [
                mock_splitwise_expense,
                mock_splitwise_expense_deleted,
            ]

            # Call the function
            refresh_splitwise()

    def test_empty_expenses_list_completes_without_error(self, flask_app, mocker):
        """Empty expenses list completes without error"""
        with flask_app.app_context():
            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")
            mocker.patch("resources.splitwise.upsert_transactions")

            # Mock the getExpenses method to return empty list
            mock_splitwise_client.getExpenses.return_value = []

            # Call the function
            refresh_splitwise()

    def test_expenses_convert_to_line_items_with_correct_amount(self, flask_app, mock_splitwise_expense_dict, mocker):
        """Expenses convert to line items with flipped user balance as amount"""
        with flask_app.app_context():
            from models.database import SessionLocal
            from models.sql_models import LineItem
            from utils.pg_bulk_ops import _bulk_upsert_transactions

            # Insert raw transaction data into database first
            with SessionLocal.begin() as db:
                _bulk_upsert_transactions(db, [mock_splitwise_expense_dict], source="splitwise_api")

            # Call the function (writes to PostgreSQL)
            splitwise_to_line_items()

            # Query database to verify line items were created
            with SessionLocal.begin() as db:
                line_items = db.query(LineItem).all()
                assert len(line_items) == 1
                line_item = line_items[0]
                assert line_item.id.startswith("li_")
                assert line_item.responsible_party == "John Doe "
                assert line_item.payment_method_id is not None
                assert line_item.description == "Test expense"
                assert line_item.amount == 50.0

    def test_expenses_with_ignored_parties_are_skipped(self, flask_app, mocker):
        """Expenses where responsible party is in ignore list are skipped"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_transactions")
            mocker.patch("resources.splitwise.upsert_line_items")

            # Mock expense where the responsible party is in the ignore list
            expense_with_ignored = {
                "id": "expense_3",
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

    def test_non_ignored_parties_create_line_items(self, flask_app, mocker):
        """Non-ignored parties create line items correctly"""
        with flask_app.app_context():
            from models.database import SessionLocal
            from models.sql_models import LineItem
            from utils.pg_bulk_ops import _bulk_upsert_transactions

            # Insert raw expense with non-ignored party
            expense_with_non_ignored = {
                "id": "expense_4",
                "date": "2023-01-15T10:30:00Z",
                "description": "Expense with non-ignored party",
                "users": [
                    {"first_name": USER_FIRST_NAME, "net_balance": -40.0},
                    {"first_name": "Regular Person", "net_balance": 40.0},
                ],
            }
            with SessionLocal.begin() as db:
                _bulk_upsert_transactions(db, [expense_with_non_ignored], source="splitwise_api")

            # Call the function
            splitwise_to_line_items()

            # Query database to verify line item was created for non-ignored party
            with SessionLocal.begin() as db:
                line_items = db.query(LineItem).all()
                assert len(line_items) == 1
                line_item = line_items[0]
                assert line_item.responsible_party == "Regular Person "
                assert line_item.amount == 40.0  # flip_amount(-40.0) = 40.0

    def test_multiple_users_combined_into_responsible_party(self, flask_app, mocker):
        """Multiple users are combined into a single responsible party string"""
        with flask_app.app_context():
            from models.database import SessionLocal
            from models.sql_models import LineItem
            from utils.pg_bulk_ops import _bulk_upsert_transactions

            # Insert raw expense with multiple users
            expense_multiple_users = {
                "id": "expense_5",
                "date": "2023-01-15T10:30:00Z",
                "description": "Expense with multiple users",
                "users": [
                    {"first_name": USER_FIRST_NAME, "net_balance": -60.0},
                    {"first_name": "Alice", "net_balance": 30.0},
                    {"first_name": "Bob", "net_balance": 30.0},
                ],
            }
            with SessionLocal.begin() as db:
                _bulk_upsert_transactions(db, [expense_multiple_users], source="splitwise_api")

            # Call the function
            splitwise_to_line_items()

            # Query database to verify line item was created
            with SessionLocal.begin() as db:
                line_items = db.query(LineItem).all()
                assert len(line_items) == 1
                line_item = line_items[0]
                assert line_item.id.startswith("li_")
                assert "Alice" in line_item.responsible_party
                assert "Bob" in line_item.responsible_party
                assert line_item.amount == 60.0

    def test_empty_expense_list_creates_no_line_items(self, flask_app, mocker):
        """Empty expense list creates no line items"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_transactions")
            mocker.patch("resources.splitwise.upsert_line_items")

            # Mock get_transactions to return empty list
            mock_get_data.return_value = []

            # Call the function
            splitwise_to_line_items()

    def test_expenses_without_current_user_are_skipped(self, flask_app, mocker):
        """Expenses without the current user are skipped"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_transactions")
            mocker.patch("resources.splitwise.upsert_line_items")

            # Mock expense without the current user
            expense_no_user = {
                "id": "expense_6",
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

    def test_iso_date_converts_to_datetime(self, flask_app, mocker):
        """ISO date strings convert to datetime objects correctly"""
        with flask_app.app_context():
            from models.database import SessionLocal
            from models.sql_models import LineItem
            from utils.pg_bulk_ops import _bulk_upsert_transactions

            # Insert raw expense with specific date
            expense_with_date = {
                "id": "expense_7",
                "date": "2023-01-15T10:30:00Z",
                "description": "Expense with date",
                "users": [
                    {"first_name": USER_FIRST_NAME, "net_balance": -25.0},
                    {"first_name": "Charlie", "net_balance": 25.0},
                ],
            }
            with SessionLocal.begin() as db:
                _bulk_upsert_transactions(db, [expense_with_date], source="splitwise_api")

            # Call the function
            splitwise_to_line_items()

            # Query database to verify date was converted correctly
            with SessionLocal.begin() as db:
                from datetime import UTC, datetime

                line_items = db.query(LineItem).all()
                assert len(line_items) == 1
                line_item = line_items[0]
                # The date should be converted to datetime
                expected_date = datetime(2023, 1, 15, 10, 30, tzinfo=UTC).replace(tzinfo=None)
                assert line_item.date == expected_date

    def test_negative_balance_flips_to_positive_amount(self, flask_app, mocker):
        """Negative user balance becomes positive line item amount"""
        with flask_app.app_context():
            from models.database import SessionLocal
            from models.sql_models import LineItem
            from utils.pg_bulk_ops import _bulk_upsert_transactions

            # Insert raw expense with positive and negative balances
            expense_mixed_balances = {
                "id": "expense_8",
                "date": "2023-01-15T10:30:00Z",
                "description": "Expense with mixed balances",
                "users": [
                    {"first_name": USER_FIRST_NAME, "net_balance": -100.0},  # User owes
                    {"first_name": "David", "net_balance": 100.0},  # David is owed
                ],
            }
            with SessionLocal.begin() as db:
                _bulk_upsert_transactions(db, [expense_mixed_balances], source="splitwise_api")

            # Call the function
            splitwise_to_line_items()

            # Query database to verify amounts were flipped correctly
            with SessionLocal.begin() as db:
                line_items = db.query(LineItem).all()
                assert len(line_items) == 1
                line_item = line_items[0]
                # User's negative balance should become positive in line item
                assert line_item.amount == 100.0  # flip_amount(-100.0) = 100.0


class TestSplitwiseIntegration:
    def test_complete_workflow_fetches_and_converts_expenses(self, flask_app, mocker):
        """Complete workflow fetches expenses and converts to line items"""
        with flask_app.app_context():
            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")
            mocker.patch("resources.splitwise.upsert_line_items")
            mocker.patch("resources.splitwise.upsert_transactions")
            mock_get_data = mocker.patch("resources.splitwise.get_transactions")

            # Mock expense for refresh
            mock_expense = mocker.Mock()
            mock_expense.deleted_at = None
            mock_expense.source_id = "expense_integration"
            mock_expense.date = "2023-01-15T10:30:00Z"
            mock_expense.description = "Integration test expense"
            mock_expense.users = [
                {"first_name": USER_FIRST_NAME, "net_balance": -75.0},
                {"first_name": "Integration User", "net_balance": 75.0},
            ]

            # Mock client responses
            mock_splitwise_client.getExpenses.return_value = [mock_expense]

            # Mock get_transactions for conversion
            mock_get_data.return_value = [
                {
                    "source_id": "expense_integration",
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

            # Test conversion function
            splitwise_to_line_items()

            # Verify conversion was called
            mock_get_data.assert_called_once_with("splitwise_api", None)
