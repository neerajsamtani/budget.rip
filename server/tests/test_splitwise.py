from unittest.mock import Mock, patch

import pytest

from constants import PARTIES_TO_IGNORE, USER_FIRST_NAME
from dao import line_items_collection, splitwise_raw_data_collection
from resources.splitwise import refresh_splitwise, splitwise_to_line_items


@pytest.fixture
def mock_splitwise_expense():
    """Mock Splitwise expense object"""
    expense = Mock()
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
def mock_splitwise_expense_deleted():
    """Mock deleted Splitwise expense object"""
    expense = Mock()
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
def mock_splitwise_expense_ignored_party():
    """Mock Splitwise expense with ignored party"""
    expense = Mock()
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
    def test_refresh_splitwise_api_success(self, test_client, jwt_token, flask_app):
        """Test GET /api/refresh/splitwise endpoint - success case"""
        with patch("resources.splitwise.refresh_splitwise") as mock_refresh, patch(
            "resources.splitwise.splitwise_to_line_items"
        ) as mock_convert:

            response = test_client.get(
                "/api/refresh/splitwise",
                headers={"Authorization": "Bearer " + jwt_token},
            )

            assert response.status_code == 200
            assert (
                response.get_data(as_text=True).strip()
                == '"Refreshed Splitwise Connection"'
            )

            # Verify both functions were called
            mock_refresh.assert_called_once()
            mock_convert.assert_called_once()

    def test_refresh_splitwise_api_unauthorized(self, test_client):
        """Test GET /api/refresh/splitwise endpoint - unauthorized"""
        response = test_client.get("/api/refresh/splitwise")

        assert response.status_code == 401


class TestSplitwiseFunctions:
    def test_refresh_splitwise_success(self, flask_app, mock_splitwise_expense):
        """Test refresh_splitwise function - success case"""
        with flask_app.app_context():
            with patch("resources.splitwise.splitwise_client") as mock_client, patch(
                "resources.splitwise.bulk_upsert"
            ) as mock_bulk_upsert:

                # Mock the getExpenses method
                mock_client.getExpenses.return_value = [mock_splitwise_expense]

                # Call the function
                refresh_splitwise()

                # Verify getExpenses was called with correct parameters
                mock_client.getExpenses.assert_called_once_with(
                    limit=1000, dated_after="2022-08-03T00:00:00Z"
                )

                # Verify bulk_upsert was called with the non-deleted expense
                mock_bulk_upsert.assert_called_once_with(
                    splitwise_raw_data_collection, [mock_splitwise_expense]
                )

    def test_refresh_splitwise_with_deleted_expense(
        self, flask_app, mock_splitwise_expense, mock_splitwise_expense_deleted
    ):
        """Test refresh_splitwise function - filters out deleted expenses"""
        with flask_app.app_context():
            with patch("resources.splitwise.splitwise_client") as mock_client, patch(
                "resources.splitwise.bulk_upsert"
            ) as mock_bulk_upsert:

                # Mock the getExpenses method to return both regular and deleted expenses
                mock_client.getExpenses.return_value = [
                    mock_splitwise_expense,
                    mock_splitwise_expense_deleted,
                ]

                # Call the function
                refresh_splitwise()

                # Verify bulk_upsert was called only with the non-deleted expense
                mock_bulk_upsert.assert_called_once_with(
                    splitwise_raw_data_collection, [mock_splitwise_expense]
                )

    def test_refresh_splitwise_no_expenses(self, flask_app):
        """Test refresh_splitwise function - no expenses returned"""
        with flask_app.app_context():
            with patch("resources.splitwise.splitwise_client") as mock_client, patch(
                "resources.splitwise.bulk_upsert"
            ) as mock_bulk_upsert:

                # Mock the getExpenses method to return empty list
                mock_client.getExpenses.return_value = []

                # Call the function
                refresh_splitwise()

                # Verify bulk_upsert was not called (no expenses to upsert)
                mock_bulk_upsert.assert_not_called()

    def test_splitwise_to_line_items_success(
        self, flask_app, mock_splitwise_expense_dict
    ):
        """Test splitwise_to_line_items function - success case"""
        with flask_app.app_context():
            with patch("resources.splitwise.get_all_data") as mock_get_data, patch(
                "resources.splitwise.bulk_upsert"
            ) as mock_bulk_upsert:

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

    def test_splitwise_to_line_items_with_ignored_party(self, flask_app):
        """Test splitwise_to_line_items function - filters out ignored parties"""
        with flask_app.app_context():
            with patch("resources.splitwise.get_all_data") as mock_get_data, patch(
                "resources.splitwise.bulk_upsert"
            ) as mock_bulk_upsert:

                # Create expense with ignored party - the responsible_party will be "Pink Palace Babes "
                # which should match PARTIES_TO_IGNORE[0] = "Pink Palace Babes"
                ignored_expense = {
                    "_id": "expense_3",
                    "date": "2023-01-15T10:30:00Z",
                    "description": "Expense with ignored party",
                    "users": [
                        {"first_name": USER_FIRST_NAME, "net_balance": -30.0},
                        {
                            "first_name": "Pink Palace Babes",  # This is in PARTIES_TO_IGNORE
                            "net_balance": 30.0,
                        },
                    ],
                }

                mock_get_data.return_value = [ignored_expense]

                # Call the function
                splitwise_to_line_items()

                # Verify bulk_upsert was not called (expense should be filtered out)
                mock_bulk_upsert.assert_not_called()

    def test_splitwise_to_line_items_with_non_ignored_party(self, flask_app):
        """Test splitwise_to_line_items function - allows non-ignored parties"""
        with flask_app.app_context():
            with patch("resources.splitwise.get_all_data") as mock_get_data, patch(
                "resources.splitwise.bulk_upsert"
            ) as mock_bulk_upsert:

                # Create expense with non-ignored party
                non_ignored_expense = {
                    "_id": "expense_4",
                    "date": "2023-01-15T10:30:00Z",
                    "description": "Expense with non-ignored party",
                    "users": [
                        {"first_name": USER_FIRST_NAME, "net_balance": -30.0},
                        {
                            "first_name": "John Doe",  # This is NOT in PARTIES_TO_IGNORE
                            "net_balance": 30.0,
                        },
                    ],
                }

                mock_get_data.return_value = [non_ignored_expense]

                # Call the function
                splitwise_to_line_items()

                # Verify bulk_upsert was called (expense should not be filtered out)
                mock_bulk_upsert.assert_called_once()
                call_args = mock_bulk_upsert.call_args
                line_items = call_args[0][1]
                assert len(line_items) == 1
                assert line_items[0].responsible_party == "John Doe "

    def test_splitwise_to_line_items_multiple_users(self, flask_app):
        """Test splitwise_to_line_items function - handles multiple users correctly"""
        with flask_app.app_context():
            with patch("resources.splitwise.get_all_data") as mock_get_data, patch(
                "resources.splitwise.bulk_upsert"
            ) as mock_bulk_upsert:

                # Create expense with multiple users
                multi_user_expense = {
                    "_id": "expense_4",
                    "date": "2023-01-15T10:30:00Z",
                    "description": "Multi-user expense",
                    "users": [
                        {"first_name": USER_FIRST_NAME, "net_balance": -100.0},
                        {"first_name": "John Doe", "net_balance": 60.0},
                        {"first_name": "Jane Smith", "net_balance": 40.0},
                    ],
                }

                mock_get_data.return_value = [multi_user_expense]

                # Call the function
                splitwise_to_line_items()

                # Verify bulk_upsert was called
                mock_bulk_upsert.assert_called_once()
                call_args = mock_bulk_upsert.call_args
                line_items = call_args[0][1]

                # Should create one line item for the current user
                assert len(line_items) == 1
                line_item = line_items[0]
                assert (
                    line_item.responsible_party == "John Doe Jane Smith "
                )  # Concatenated names
                assert line_item.amount == 100.0  # flip_amount(-100.0) = 100.0

    def test_splitwise_to_line_items_no_expenses(self, flask_app):
        """Test splitwise_to_line_items function - no expenses to process"""
        with flask_app.app_context():
            with patch("resources.splitwise.get_all_data") as mock_get_data, patch(
                "resources.splitwise.bulk_upsert"
            ) as mock_bulk_upsert:

                # Mock get_all_data to return empty list
                mock_get_data.return_value = []

                # Call the function
                splitwise_to_line_items()

                # Verify bulk_upsert was not called
                mock_bulk_upsert.assert_not_called()

    def test_splitwise_to_line_items_user_not_found(self, flask_app):
        """Test splitwise_to_line_items function - current user not found in expense"""
        with flask_app.app_context():
            with patch("resources.splitwise.get_all_data") as mock_get_data, patch(
                "resources.splitwise.bulk_upsert"
            ) as mock_bulk_upsert:

                # Create expense without current user
                other_user_expense = {
                    "_id": "expense_5",
                    "date": "2023-01-15T10:30:00Z",
                    "description": "Other user expense",
                    "users": [
                        {"first_name": "John Doe", "net_balance": 50.0},
                        {"first_name": "Jane Smith", "net_balance": -50.0},
                    ],
                }

                mock_get_data.return_value = [other_user_expense]

                # Call the function
                splitwise_to_line_items()

                # Verify bulk_upsert was not called (no line item should be created)
                mock_bulk_upsert.assert_not_called()

    def test_splitwise_to_line_items_date_conversion(self, flask_app):
        """Test splitwise_to_line_items function - date conversion works correctly"""
        with flask_app.app_context():
            with patch("resources.splitwise.get_all_data") as mock_get_data, patch(
                "resources.splitwise.bulk_upsert"
            ) as mock_bulk_upsert, patch(
                "resources.splitwise.iso_8601_to_posix"
            ) as mock_date_convert:

                # Mock date conversion
                mock_date_convert.return_value = 1673778600.0  # Fixed timestamp

                expense = {
                    "_id": "expense_6",
                    "date": "2023-01-15T10:30:00Z",
                    "description": "Test expense",
                    "users": [
                        {"first_name": USER_FIRST_NAME, "net_balance": -25.0},
                        {"first_name": "John Doe", "net_balance": 25.0},
                    ],
                }

                mock_get_data.return_value = [expense]

                # Call the function
                splitwise_to_line_items()

                # Verify date conversion was called
                mock_date_convert.assert_called_once_with("2023-01-15T10:30:00Z")

                # Verify line item has correct date
                call_args = mock_bulk_upsert.call_args
                line_items = call_args[0][1]
                assert line_items[0].date == 1673778600.0

    def test_splitwise_to_line_items_amount_flipping(self, flask_app):
        """Test splitwise_to_line_items function - amount flipping works correctly"""
        with flask_app.app_context():
            with patch("resources.splitwise.get_all_data") as mock_get_data, patch(
                "resources.splitwise.bulk_upsert"
            ) as mock_bulk_upsert, patch(
                "resources.splitwise.flip_amount"
            ) as mock_flip:

                # Mock flip_amount to return positive value
                mock_flip.return_value = 75.0

                expense = {
                    "_id": "expense_7",
                    "date": "2023-01-15T10:30:00Z",
                    "description": "Test expense",
                    "users": [
                        {"first_name": USER_FIRST_NAME, "net_balance": -75.0},
                        {"first_name": "John Doe", "net_balance": 75.0},
                    ],
                }

                mock_get_data.return_value = [expense]

                # Call the function
                splitwise_to_line_items()

                # Verify flip_amount was called with correct value
                mock_flip.assert_called_once_with(-75.0)

                # Verify line item has flipped amount
                call_args = mock_bulk_upsert.call_args
                line_items = call_args[0][1]
                assert line_items[0].amount == 75.0


class TestSplitwiseIntegration:
    def test_full_refresh_workflow(self, flask_app):
        """Test the complete refresh workflow from API to database"""
        with flask_app.app_context():
            with patch("resources.splitwise.splitwise_client") as mock_client, patch(
                "resources.splitwise.bulk_upsert"
            ) as mock_bulk_upsert:

                # Mock expense data
                expense = Mock()
                expense.deleted_at = None
                expense._id = "expense_1"
                expense.date = "2023-01-15T10:30:00Z"
                expense.description = "Integration test expense"
                expense.users = [
                    {"first_name": USER_FIRST_NAME, "net_balance": -100.0},
                    {"first_name": "John Doe", "net_balance": 100.0},
                ]

                mock_client.getExpenses.return_value = [expense]

                # Call refresh function
                refresh_splitwise()

                # Verify expense was stored
                mock_bulk_upsert.assert_called_with(
                    splitwise_raw_data_collection, [expense]
                )

                # Reset mock for next call
                mock_bulk_upsert.reset_mock()

                # Mock get_all_data to return the stored expense
                with patch("resources.splitwise.get_all_data") as mock_get_data:
                    mock_get_data.return_value = [expense.__dict__]

                    # Call conversion function
                    splitwise_to_line_items()

                    # Verify line items were created
                    mock_bulk_upsert.assert_called_once()
                    call_args = mock_bulk_upsert.call_args
                    assert call_args[0][0] == line_items_collection

                    line_items = call_args[0][1]
                    assert len(line_items) == 1
                    assert line_items[0].description == "Integration test expense"
                    assert line_items[0].payment_method == "Splitwise"
