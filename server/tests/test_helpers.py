import unittest
from datetime import datetime

import helpers


class TestISO8601ToReadable(unittest.TestCase):
    def test_conversion(self):
        # Test that the function correctly converts the input ISO 8601 date string
        # to a readable date string in the format "%b %d %Y".
        input_date = "2022-03-28T10:00:00"
        expected_output = "Mar 28 2022"
        self.assertEqual(helpers.iso_8601_to_readable(input_date), expected_output)

    def test_invalid_input(self):
        # Test that the function raises a ValueError when an invalid input is provided.
        # In this case, an invalid input is a string that does not contain a time component.
        input_date = "2022-03-28"
        with self.assertRaises(ValueError):
            helpers.iso_8601_to_readable(input_date)


class TestHtmlDateToPosix(unittest.TestCase):
    def test_html_date_to_posix(self):
        # Test that the function correctly converts an HTML date string to a POSIX timestamp.
        input_date = "2023-03-28"
        expected_output = datetime(2023, 3, 28).timestamp()
        self.assertEqual(helpers.html_date_to_posix(input_date), expected_output)

    def test_html_date_to_posix_invalid_input(self):
        # Test that the function raises a ValueError when an invalid input is provided.
        # In this case, an invalid input is a string that is not in the expected format.
        input_date = "2022/03/28"
        with self.assertRaises(ValueError):
            helpers.html_date_to_posix(input_date)


if __name__ == "__main__":
    unittest.main()
