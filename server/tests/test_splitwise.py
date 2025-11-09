import pytest

from constants import PARTIES_TO_IGNORE, USER_FIRST_NAME
from dao import line_items_collection, splitwise_raw_data_collection
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
            mock_bulk_upsert = mocker.patch("resources.splitwise.bulk_upsert")

            # Mock bulk_upsert_transactions (PostgreSQL)
            mocker.patch("resources.splitwise.bulk_upsert_transactions")

            # Mock the getExpenses method
            mock_splitwise_client.getExpenses.return_value = [mock_splitwise_expense]

            # Call the function
            refresh_splitwise()

            # Verify getExpenses was called with correct parameters
            mock_splitwise_client.getExpenses.assert_called_once_with(limit=1000, dated_after="2022-08-03T00:00:00Z")

            # Verify bulk_upsert was called with the non-deleted expense
            mock_bulk_upsert.assert_called_once_with(splitwise_raw_data_collection, [mock_splitwise_expense])

    def test_refresh_splitwise_with_deleted_expense(
        self, flask_app, mock_splitwise_expense, mock_splitwise_expense_deleted, mocker
    ):
        """Test refresh_splitwise function - filters out deleted expenses"""
        with flask_app.app_context():
            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")
            # Mock bulk_upsert (MongoDB)
            mock_bulk_upsert = mocker.patch("resources.splitwise.bulk_upsert")

            # Mock bulk_upsert_transactions (PostgreSQL)
            mocker.patch("resources.splitwise.bulk_upsert_transactions")

            # Mock the getExpenses method to return both regular and deleted expenses
            mock_splitwise_client.getExpenses.return_value = [
                mock_splitwise_expense,
                mock_splitwise_expense_deleted,
            ]

            # Call the function
            refresh_splitwise()

            # Verify bulk_upsert was called only with the non-deleted expense
            mock_bulk_upsert.assert_called_once_with(splitwise_raw_data_collection, [mock_splitwise_expense])

    def test_refresh_splitwise_no_expenses(self, flask_app, mocker):
        """Test refresh_splitwise function - no expenses returned"""
        with flask_app.app_context():
            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")
            # Mock bulk_upsert (MongoDB)
            mock_bulk_upsert = mocker.patch("resources.splitwise.bulk_upsert")

            # Mock bulk_upsert_transactions (PostgreSQL)
            mocker.patch("resources.splitwise.bulk_upsert_transactions")

            # Mock the getExpenses method to return empty list
            mock_splitwise_client.getExpenses.return_value = []

            # Call the function
            refresh_splitwise()

            # Verify bulk_upsert was not called (no expenses to upsert)
            mock_bulk_upsert.assert_not_called()

    def test_splitwise_to_line_items_success(self, flask_app, mock_splitwise_expense_dict, mocker):
        """Test splitwise_to_line_items function - success case"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_all_data")
            # Mock bulk_upsert (MongoDB)
            mock_bulk_upsert = mocker.patch("resources.splitwise.bulk_upsert")

            # Mock bulk_upsert_line_items (PostgreSQL)
            mocker.patch("resources.splitwise.bulk_upsert_line_items")

            # Mock get_all_data to return our test expense
            mock_get_data.return_value = [mock_splitwise_expense_dict]

            # Call the function
            splitwise_to_line_items()

            # Verify get_all_data was called
            mock_get_data.assert_called_once_with(splitwise_raw_data_collection)

            # Verify bulk_upsert was called with line items
            mock_bulk_upsert.assert_called_once()
            call_args = mock_bulk_upsert.call_args
            assert call_args[0][0] == line_items_collection

            # Check that line items were created correctly
            line_items = call_args[0][1]
            assert len(line_items) == 1

            line_item = line_items[0]
            assert line_item.id == "line_item_expense_1"
            assert line_item.responsible_party == "John Doe "
            assert line_item.payment_method == "Splitwise"
            assert line_item.description == "Test expense"
            assert line_item.amount == 50.0  # flip_amount(-50.0) = 50.0

    def test_splitwise_to_line_items_with_ignored_party(self, flask_app, mocker):
        """Test splitwise_to_line_items function - filters out ignored parties"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_all_data")
            # Mock bulk_upsert (MongoDB)
            mock_bulk_upsert = mocker.patch("resources.splitwise.bulk_upsert")

            # Mock bulk_upsert_line_items (PostgreSQL)
            mocker.patch("resources.splitwise.bulk_upsert_line_items")

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
            mock_bulk_upsert.assert_not_called()

    def test_splitwise_to_line_items_with_non_ignored_party(self, flask_app, mocker):
        """Test splitwise_to_line_items function - handles non-ignored parties correctly"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_all_data")
            # Mock bulk_upsert (MongoDB)
            mock_bulk_upsert = mocker.patch("resources.splitwise.bulk_upsert")

            # Mock bulk_upsert_line_items (PostgreSQL)
            mocker.patch("resources.splitwise.bulk_upsert_line_items")

            # Mock expense with non-ignored party
            expense_with_non_ignored = {
                "_id": "expense_4",
                "date": "2023-01-15T10:30:00Z",
                "description": "Expense with non-ignored party",
                "users": [
                    {"first_name": USER_FIRST_NAME, "net_balance": -40.0},
                    {"first_name": "Regular Person", "net_balance": 40.0},
                ],
            }
            mock_get_data.return_value = [expense_with_non_ignored]

            # Call the function
            splitwise_to_line_items()

            # Verify bulk_upsert was called with line items
            mock_bulk_upsert.assert_called_once()
            call_args = mock_bulk_upsert.call_args
            line_items = call_args[0][1]

            # Should create line item for the non-ignored party
            assert len(line_items) == 1
            line_item = line_items[0]
            assert line_item.responsible_party == "Regular Person "
            assert line_item.amount == 40.0  # flip_amount(-40.0) = 40.0

    def test_splitwise_to_line_items_multiple_users(self, flask_app, mocker):
        """Test splitwise_to_line_items function - handles multiple users correctly"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_all_data")
            # Mock bulk_upsert (MongoDB)
            mock_bulk_upsert = mocker.patch("resources.splitwise.bulk_upsert")

            # Mock bulk_upsert_line_items (PostgreSQL)
            mocker.patch("resources.splitwise.bulk_upsert_line_items")

            # Mock expense with multiple users
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
            mock_get_data.return_value = [expense_multiple_users]

            # Call the function
            splitwise_to_line_items()

            # Verify bulk_upsert was called with line items
            mock_bulk_upsert.assert_called_once()
            call_args = mock_bulk_upsert.call_args
            line_items = call_args[0][1]

            # Should create one line item for the current user (Neeraj) with combined responsible parties
            assert len(line_items) == 1
            line_item = line_items[0]
            assert line_item.id == "line_item_expense_5"
            # The responsible party should be "Alice Bob " (both non-current users)
            assert "Alice" in line_item.responsible_party
            assert "Bob" in line_item.responsible_party
            assert line_item.amount == 60.0  # flip_amount(-60.0) = 60.0

    def test_splitwise_to_line_items_no_expenses(self, flask_app, mocker):
        """Test splitwise_to_line_items function - no expenses to process"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_all_data")
            # Mock bulk_upsert (MongoDB)
            mock_bulk_upsert = mocker.patch("resources.splitwise.bulk_upsert")

            # Mock bulk_upsert_line_items (PostgreSQL)
            mocker.patch("resources.splitwise.bulk_upsert_line_items")

            # Mock get_all_data to return empty list
            mock_get_data.return_value = []

            # Call the function
            splitwise_to_line_items()

            # Verify bulk_upsert was not called
            mock_bulk_upsert.assert_not_called()

    def test_splitwise_to_line_items_user_not_found(self, flask_app, mocker):
        """Test splitwise_to_line_items function - user not found in expense"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_all_data")
            # Mock bulk_upsert (MongoDB)
            mock_bulk_upsert = mocker.patch("resources.splitwise.bulk_upsert")

            # Mock bulk_upsert_line_items (PostgreSQL)
            mocker.patch("resources.splitwise.bulk_upsert_line_items")

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
            mock_bulk_upsert.assert_not_called()

    def test_splitwise_to_line_items_date_conversion(self, flask_app, mocker):
        """Test splitwise_to_line_items function - date conversion"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_all_data")
            # Mock bulk_upsert (MongoDB)
            mock_bulk_upsert = mocker.patch("resources.splitwise.bulk_upsert")

            # Mock bulk_upsert_line_items (PostgreSQL)
            mocker.patch("resources.splitwise.bulk_upsert_line_items")

            # Mock expense with specific date
            expense_with_date = {
                "_id": "expense_7",
                "date": "2023-01-15T10:30:00Z",
                "description": "Expense with date",
                "users": [
                    {"first_name": USER_FIRST_NAME, "net_balance": -25.0},
                    {"first_name": "Charlie", "net_balance": 25.0},
                ],
            }
            mock_get_data.return_value = [expense_with_date]

            # Call the function
            splitwise_to_line_items()

            # Verify bulk_upsert was called
            mock_bulk_upsert.assert_called_once()
            call_args = mock_bulk_upsert.call_args
            line_items = call_args[0][1]

            # Check that date was converted correctly
            assert len(line_items) == 1
            line_item = line_items[0]
            # The date should be converted to timestamp
            assert line_item.date == 1673778600.0  # 2023-01-15T10:30:00Z as timestamp

    def test_splitwise_to_line_items_amount_flipping(self, flask_app, mocker):
        """Test splitwise_to_line_items function - amount flipping logic"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_all_data")
            # Mock bulk_upsert (MongoDB)
            mock_bulk_upsert = mocker.patch("resources.splitwise.bulk_upsert")

            # Mock bulk_upsert_line_items (PostgreSQL)
            mocker.patch("resources.splitwise.bulk_upsert_line_items")

            # Mock expense with positive and negative balances
            expense_mixed_balances = {
                "_id": "expense_8",
                "date": "2023-01-15T10:30:00Z",
                "description": "Expense with mixed balances",
                "users": [
                    {"first_name": USER_FIRST_NAME, "net_balance": -100.0},  # User owes
                    {"first_name": "David", "net_balance": 100.0},  # David is owed
                ],
            }
            mock_get_data.return_value = [expense_mixed_balances]

            # Call the function
            splitwise_to_line_items()

            # Verify bulk_upsert was called
            mock_bulk_upsert.assert_called_once()
            call_args = mock_bulk_upsert.call_args
            line_items = call_args[0][1]

            # Check that amounts were flipped correctly
            assert len(line_items) == 1
            line_item = line_items[0]
            # User's negative balance should become positive in line item
            assert line_item.amount == 100.0  # flip_amount(-100.0) = 100.0


class TestSplitwiseDualWrite:
    """Test dual-write functionality for Splitwise endpoints"""

    def test_refresh_splitwise_calls_dual_write_for_transactions(self, flask_app, mocker):
        """Test that refresh_splitwise uses dual_write_operation for transactions"""
        with flask_app.app_context():
            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")

            # Mock expense
            mock_expense = mocker.Mock()
            mock_expense.deleted_at = None
            mock_expense._id = "expense_test"
            mock_expense.date = "2023-01-15T10:30:00Z"
            mock_expense.description = "Test expense"

            # Mock client response
            mock_splitwise_client.getExpenses.return_value = [mock_expense]

            # Mock dual_write_operation
            mock_dual_write = mocker.patch("resources.splitwise.dual_write_operation")
            mock_dual_write.return_value = {
                "success": True,
                "mongo_success": True,
                "pg_success": True,
            }

            # Call refresh_splitwise
            refresh_splitwise()

            # Verify dual_write_operation was called
            mock_dual_write.assert_called_once()
            call_kwargs = mock_dual_write.call_args[1]

            # Verify operation name
            assert call_kwargs["operation_name"] == "splitwise_refresh_transactions"

            # Verify mongo_write_func and pg_write_func are callables
            assert callable(call_kwargs["mongo_write_func"])
            assert callable(call_kwargs["pg_write_func"])

    def test_splitwise_to_line_items_calls_dual_write(self, flask_app, mocker):
        """Test that splitwise_to_line_items uses dual_write_operation"""
        with flask_app.app_context():
            mock_get_data = mocker.patch("resources.splitwise.get_all_data")

            # Mock expense data
            expense_data = {
                "_id": "expense_test",
                "date": "2023-01-15T10:30:00Z",
                "description": "Test expense",
                "users": [
                    {"first_name": USER_FIRST_NAME, "net_balance": -50.0},
                    {"first_name": "Test User", "net_balance": 50.0},
                ],
            }
            mock_get_data.return_value = [expense_data]

            # Mock dual_write_operation
            mock_dual_write = mocker.patch("resources.splitwise.dual_write_operation")
            mock_dual_write.return_value = {
                "success": True,
                "mongo_success": True,
                "pg_success": True,
            }

            # Call splitwise_to_line_items
            splitwise_to_line_items()

            # Verify dual_write_operation was called
            mock_dual_write.assert_called_once()
            call_kwargs = mock_dual_write.call_args[1]

            # Verify operation name
            assert call_kwargs["operation_name"] == "splitwise_create_line_items"

            # Verify both write functions are callables
            assert callable(call_kwargs["mongo_write_func"])
            assert callable(call_kwargs["pg_write_func"])

    def test_splitwise_dual_write_error_handling(self, flask_app, mocker):
        """Test error handling in dual-write for Splitwise"""
        with flask_app.app_context():
            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")

            # Mock expense
            mock_expense = mocker.Mock()
            mock_expense.deleted_at = None
            mock_expense._id = "expense_test"

            # Mock client response
            mock_splitwise_client.getExpenses.return_value = [mock_expense]

            # Mock dual_write_operation to simulate MongoDB failure
            from utils.dual_write import DualWriteError

            mock_dual_write = mocker.patch("resources.splitwise.dual_write_operation")
            mock_dual_write.side_effect = DualWriteError("MongoDB write failed")

            # Call refresh_splitwise and expect exception
            with pytest.raises(DualWriteError):
                refresh_splitwise()

    def test_splitwise_dual_write_pg_failure_continues(self, flask_app, mocker):
        """Test that PostgreSQL failure in dual-write logs but continues"""
        with flask_app.app_context():
            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")

            # Mock expense
            mock_expense = mocker.Mock()
            mock_expense.deleted_at = None
            mock_expense._id = "expense_test"

            # Mock client response
            mock_splitwise_client.getExpenses.return_value = [mock_expense]

            # Mock dual_write_operation to simulate PG failure (non-critical)
            mock_dual_write = mocker.patch("resources.splitwise.dual_write_operation")
            mock_dual_write.return_value = {
                "success": True,  # Still success because MongoDB succeeded
                "mongo_success": True,
                "pg_success": False,
                "pg_error": "PostgreSQL connection failed",
            }

            # Call refresh_splitwise - should not raise
            refresh_splitwise()  # Should complete without exception

            # Verify dual_write was called
            mock_dual_write.assert_called_once()


class TestSplitwiseIntegration:
    def test_full_refresh_workflow(self, flask_app, mocker):
        """Test the complete refresh workflow from API to database"""
        with flask_app.app_context():
            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")
            # Mock bulk_upsert (MongoDB)
            # Mock bulk_upsert (MongoDB)
            mock_bulk_upsert = mocker.patch("resources.splitwise.bulk_upsert")

            # Mock bulk_upsert_line_items (PostgreSQL)
            mocker.patch("resources.splitwise.bulk_upsert_line_items")

            # Mock bulk_upsert_transactions (PostgreSQL)
            mocker.patch("resources.splitwise.bulk_upsert_transactions")
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
            assert mock_bulk_upsert.call_count == 1

            # Reset mock for conversion test
            mock_bulk_upsert.reset_mock()

            # Test conversion function
            splitwise_to_line_items()

            # Verify conversion was called
            mock_get_data.assert_called_once_with(splitwise_raw_data_collection)
            assert mock_bulk_upsert.call_count == 1

            # Verify line items were created correctly
            call_args = mock_bulk_upsert.call_args
            line_items = call_args[0][1]
            assert len(line_items) == 1
            assert line_items[0].description == "Integration test expense"
            assert line_items[0].amount == 75.0
