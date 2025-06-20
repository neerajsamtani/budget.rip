from datetime import datetime

import pytest

import helpers
from resources.line_item import LineItem


@pytest.mark.parametrize(
    "input_amount, expected_result",
    [
        (10.0, -10.0),
        (-5.0, 5.0),
        (0.0, 0.0),
    ],
)
def test_flip_amount(input_amount, expected_result):
    assert helpers.flip_amount(input_amount) == expected_result


def test_flip_amount_with_string_amount():
    with pytest.raises(ValueError):
        helpers.flip_amount("invalid_input")  # type: ignore


def test_to_dict():
    input_line_item = LineItem(
        id="1234",
        date=1648339200.0,  # 2022-03-27 as timestamp
        responsible_party="John Smith",
        payment_method="Venmo",
        description="Groceries",
        amount=50.0,
    )

    expected_dict = {
        "id": "1234",
        "date": 1648339200.0,
        "responsible_party": "John Smith",
        "payment_method": "Venmo",
        "description": "Groceries",
        "amount": 50.0,
    }

    assert helpers.to_dict(input_line_item) == expected_dict


@pytest.mark.parametrize(
    "input_date, expected_output",
    [
        ("2022-03-28T10:00:00", "Mar 28 2022"),
        ("2022-03-28", None),  # Invalid input, expecting None
    ],
)
def test_iso_8601_to_readable(input_date, expected_output):
    if expected_output is not None:
        assert helpers.iso_8601_to_readable(input_date) == expected_output
    else:
        with pytest.raises(ValueError):
            helpers.iso_8601_to_readable(input_date)


@pytest.mark.parametrize(
    "input_date, expected_output",
    [
        ("2023-03-28", datetime(2023, 3, 28).timestamp()),
        ("2022/03/28", None),  # Invalid input, expecting None
    ],
)
def test_html_date_to_posix(input_date, expected_output):
    if expected_output is not None:
        assert helpers.html_date_to_posix(input_date) == expected_output
    else:
        with pytest.raises(ValueError):
            helpers.html_date_to_posix(input_date)


@pytest.mark.parametrize(
    "input_timestamp, expected_output",
    [
        (1617053994.0, "Mar 29 2021"),
        ("not a float", None),  # Invalid input, expecting None
    ],
)
def test_posix_to_readable(input_timestamp, expected_output):
    if expected_output is not None:
        assert helpers.posix_to_readable(input_timestamp) == expected_output
    else:
        with pytest.raises(TypeError):
            helpers.posix_to_readable(input_timestamp)


@pytest.mark.parametrize(
    "iso_date, expected_output",
    [
        (
            "2022-03-28T10:15:30+00:00",
            1648462530.0,
        ),  # Test with timezone offset
        (
            "2023-01-15T10:30:00Z",
            1673778600.0,
        ),  # Test with Z timezone indicator
        ("2022/03/28", None),  # Invalid input, expecting None
    ],
)
def test_iso_8601_to_posix(iso_date, expected_output):
    if expected_output is not None:
        assert helpers.iso_8601_to_posix(iso_date) == expected_output
    else:
        with pytest.raises(ValueError):
            helpers.iso_8601_to_posix(iso_date)


def test_sort_by_date_descending():
    line_items = [
        LineItem(
            "1", datetime(2022, 1, 1).timestamp(), "John", "Venmo", "item 1", 100.0
        ).__dict__,
        LineItem(
            "2", datetime(2022, 2, 1).timestamp(), "Mary", "Splitwise", "item 2", 50.0
        ).__dict__,
        LineItem(
            "3", datetime(2021, 12, 31).timestamp(), "Jane", "Cash", "item 3", 75.0
        ).__dict__,
    ]

    sorted_items = helpers.sort_by_date_descending(line_items)

    assert sorted_items[0]["id"] == "2"
    assert sorted_items[1]["id"] == "1"
    assert sorted_items[2]["id"] == "3"


class MockVenmoClient:
    def get_access_token(self, username, password):
        return "test_access_token"


@pytest.fixture
def mock_venmo_client(monkeypatch):
    def mock_get_access_token(username, password):
        return "test_access_token"

    mock_client = MockVenmoClient()
    monkeypatch.setattr(mock_client, "get_access_token", mock_get_access_token)
    return mock_client


def test_get_venmo_access_token(mock_venmo_client, monkeypatch):
    username = "test_username"
    password = "test_password"

    monkeypatch.setattr(helpers, "VenmoClient", lambda: mock_venmo_client)

    access_token = helpers.get_venmo_access_token(username, password, mock_venmo_client)

    assert access_token == "test_access_token"
