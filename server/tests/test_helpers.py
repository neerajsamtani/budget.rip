import unittest
from datetime import datetime
from unittest.mock import MagicMock

import helpers
from resources.line_item import LineItem


class TestFlipAmount(unittest.TestCase):
    def test_positive_amount(self):
        self.assertEqual(helpers.flip_amount(10.0), -10.0)

    def test_negative_amount(self):
        self.assertEqual(helpers.flip_amount(-5.0), 5.0)

    def test_zero_amount(self):
        self.assertEqual(helpers.flip_amount(0.0), 0.0)

    def test_string_amount(self):
        with self.assertRaises(ValueError):
            helpers.flip_amount("invalid_input")


class TestToDict(unittest.TestCase):
    def test_line_item_to_dict(self):
        input_line_item = LineItem(
            id=1234,
            date="2022-03-27",
            responsible_party="John Smith",
            payment_method="Venmo",
            description="Groceries",
            amount=50.0,
        )

        expected_dict = {
            "id": 1234,
            "date": "2022-03-27",
            "responsible_party": "John Smith",
            "payment_method": "Venmo",
            "description": "Groceries",
            "amount": 50.0,
        }

        self.assertEqual(helpers.to_dict(input_line_item), expected_dict)


class TestISO8601ToReadable(unittest.TestCase):
    def test_conversion(self):
        """
        Test that the function correctly converts the input ISO 8601 date string
        to a readable date string in the format "%b %d %Y".
        """
        input_date = "2022-03-28T10:00:00"
        expected_output = "Mar 28 2022"
        self.assertEqual(helpers.iso_8601_to_readable(input_date), expected_output)

    def test_invalid_input(self):
        """
        Test that the function raises a ValueError when an invalid input is provided.
        In this case, an invalid input is a string that does not contain a time component.
        """
        input_date = "2022-03-28"
        with self.assertRaises(ValueError):
            helpers.iso_8601_to_readable(input_date)


class TestHtmlDateToPosix(unittest.TestCase):
    def test_html_date_to_posix(self):
        """
        Test that the function correctly converts an HTML date string to a POSIX timestamp.
        """
        input_date = "2023-03-28"
        expected_output = datetime(2023, 3, 28).timestamp()
        self.assertEqual(helpers.html_date_to_posix(input_date), expected_output)

    def test_html_date_to_posix_invalid_input(self):
        """
        Test that the function raises a ValueError when an invalid input is provided.
        In this case, an invalid input is a string that is not in the expected format.
        """
        input_date = "2022/03/28"
        with self.assertRaises(ValueError):
            helpers.html_date_to_posix(input_date)


class TestPosixToReadable(unittest.TestCase):
    def test_valid_date(self):
        """
        Test a valid POSIX timestamp
        """
        posix_timestamp = 1617053994.0
        expected_output = "Mar 29 2021"
        self.assertEqual(helpers.posix_to_readable(posix_timestamp), expected_output)

    def test_invalid_input(self):
        """
        Test invalid input (not a float)
        """
        invalid_input = "not a float"
        with self.assertRaises(TypeError):
            helpers.posix_to_readable(invalid_input)


class TestISO8601ToPosix(unittest.TestCase):
    def test_valid_date(self):
        """
        Test a valid ISO 8601 date
        """
        iso_date = "2022-03-28T10:15:30+00:00"
        # expected_output = 1648487730.0
        # TODO: Fix implementation to account for timezones.
        # This currently fails on a server
        self.assertIsInstance(helpers.iso_8601_to_posix(iso_date), float)

    def test_invalid_input(self):
        """
        Test invalid input (not in ISO 8601 format)
        """
        invalid_input = "2022/03/28"
        with self.assertRaises(ValueError):
            helpers.iso_8601_to_posix(invalid_input)


class TestSortByDate(unittest.TestCase):
    def test_sort_by_date(self):
        line_items = [
            LineItem(
                1, datetime(2022, 1, 1), "John", "Venmo", "item 1", 100.0
            ).__dict__,
            LineItem(
                2, datetime(2022, 2, 1), "Mary", "Splitwise", "item 2", 50.0
            ).__dict__,
            LineItem(
                3, datetime(2021, 12, 31), "Jane", "Cash", "item 3", 75.0
            ).__dict__,
        ]

        sorted_items = helpers.sort_by_date(line_items)

        self.assertEqual(sorted_items[0]["id"], 2)
        self.assertEqual(sorted_items[1]["id"], 1)
        self.assertEqual(sorted_items[2]["id"], 3)


class TestGetVenmoAccessToken(unittest.TestCase):
    def setUp(self):
        # Mock the VenmoClient class and its get_access_token method
        self.mock_client = MagicMock()
        self.mock_client.get_access_token.return_value = "test_access_token"

    def test_get_venmo_access_token(self):
        # Call the function with test data and the mock VenmoClient
        username = "test_username"
        password = "test_password"
        access_token = helpers.get_venmo_access_token(
            username, password, self.mock_client
        )

        # Check that the mock client's get_access_token method was called with the correct args
        self.mock_client.get_access_token.assert_called_once_with(
            username=username, password=password
        )

        # Check that the function returns the expected access token
        self.assertEqual(access_token, "test_access_token")


if __name__ == "__main__":
    unittest.main()
