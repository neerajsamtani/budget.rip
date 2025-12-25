"""Tests for validation utilities."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from utils.validation import (
    require_field,
    validate_amount,
    validate_date_to_timestamp,
    validate_posix_timestamp,
)


class TestRequireField:
    """Tests for require_field function."""

    def test_require_field_present(self):
        """Test that require_field returns value when field exists."""
        data = {"name": "John", "age": 30}
        assert require_field(data, "name", "test data") == "John"
        assert require_field(data, "age", "test data") == 30

    def test_require_field_missing(self):
        """Test that require_field raises ValueError when field is missing."""
        data = {"name": "John"}
        with pytest.raises(ValueError, match="Missing required field 'age'"):
            require_field(data, "age", "test data")

    def test_require_field_context_message(self):
        """Test that error message includes context."""
        data = {}
        with pytest.raises(ValueError, match="in Venmo transaction"):
            require_field(data, "date_created", "Venmo transaction")

    def test_require_field_shows_available_fields(self):
        """Test that error message shows available fields."""
        data = {"name": "John", "email": "john@example.com"}
        with pytest.raises(ValueError, match="Available fields"):
            require_field(data, "age", "user data")


class TestValidatePosixTimestamp:
    """Tests for validate_posix_timestamp function."""

    def test_validate_posix_timestamp_valid_int(self):
        """Test validation with valid integer timestamp."""
        timestamp = 1704067200  # 2024-01-01 00:00:00 UTC
        result = validate_posix_timestamp(timestamp, "date_created")
        assert result == 1704067200.0
        assert isinstance(result, float)

    def test_validate_posix_timestamp_valid_float(self):
        """Test validation with valid float timestamp."""
        timestamp = 1704067200.5
        result = validate_posix_timestamp(timestamp, "date_created")
        assert result == 1704067200.5

    def test_validate_posix_timestamp_valid_string(self):
        """Test validation with valid string timestamp."""
        timestamp = "1704067200"
        result = validate_posix_timestamp(timestamp, "date_created")
        assert result == 1704067200.0

    def test_validate_posix_timestamp_negative(self):
        """Test that negative timestamps raise ValueError."""
        with pytest.raises(ValueError, match="Timestamp cannot be negative"):
            validate_posix_timestamp(-100, "date_created")

    def test_validate_posix_timestamp_invalid_string(self):
        """Test that non-numeric strings raise ValueError."""
        with pytest.raises(ValueError, match="Invalid timestamp for 'date_created'"):
            validate_posix_timestamp("not a number", "date_created")

    def test_validate_posix_timestamp_none(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match="Invalid timestamp"):
            validate_posix_timestamp(None, "date_created")


class TestValidateAmount:
    """Tests for validate_amount function."""

    def test_validate_amount_valid_int(self):
        """Test validation with valid integer amount."""
        result = validate_amount(100, "amount")
        assert result == Decimal("100")
        assert isinstance(result, Decimal)

    def test_validate_amount_valid_float(self):
        """Test validation with valid float amount."""
        result = validate_amount(99.99, "amount")
        assert result == Decimal("99.99")

    def test_validate_amount_valid_string(self):
        """Test validation with valid string amount."""
        result = validate_amount("123.45", "amount")
        assert result == Decimal("123.45")

    def test_validate_amount_negative(self):
        """Test that negative amounts are allowed (for refunds/credits)."""
        result = validate_amount(-50.00, "amount")
        assert result == Decimal("-50.00")

    def test_validate_amount_zero(self):
        """Test that zero amount is allowed."""
        result = validate_amount(0, "amount")
        assert result == Decimal("0")

    def test_validate_amount_invalid_string(self):
        """Test that non-numeric strings raise ValueError."""
        with pytest.raises(ValueError, match="Invalid amount for 'amount'"):
            validate_amount("not a number", "amount")

    def test_validate_amount_none(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount(None, "amount")


class TestValidateDateToTimestamp:
    """Tests for validate_date_to_timestamp function."""

    def test_validate_date_timestamp_int(self):
        """Test conversion from integer POSIX timestamp."""
        timestamp = 1704067200
        result = validate_date_to_timestamp(timestamp, "date")
        assert isinstance(result, datetime)
        assert result.tzinfo == UTC
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1

    def test_validate_date_timestamp_float(self):
        """Test conversion from float POSIX timestamp."""
        timestamp = 1704067200.5
        result = validate_date_to_timestamp(timestamp, "date")
        assert isinstance(result, datetime)
        assert result.tzinfo == UTC

    def test_validate_date_datetime_naive(self):
        """Test conversion from naive datetime (adds UTC)."""
        dt = datetime(2024, 1, 1, 0, 0, 0)
        result = validate_date_to_timestamp(dt, "date")
        assert isinstance(result, datetime)
        assert result.tzinfo == UTC
        assert result.year == 2024

    def test_validate_date_datetime_aware(self):
        """Test conversion from aware datetime."""
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        result = validate_date_to_timestamp(dt, "date")
        assert isinstance(result, datetime)
        assert result.tzinfo == UTC
        assert result == dt

    def test_validate_date_iso_string(self):
        """Test conversion from ISO 8601 string."""
        iso_date = "2024-01-01T00:00:00Z"
        result = validate_date_to_timestamp(iso_date, "date")
        assert isinstance(result, datetime)
        assert result.tzinfo == UTC
        assert result.year == 2024
        assert result.month == 1

    def test_validate_date_iso_string_with_offset(self):
        """Test conversion from ISO 8601 string with timezone offset."""
        iso_date = "2024-01-01T00:00:00+00:00"
        result = validate_date_to_timestamp(iso_date, "date")
        assert isinstance(result, datetime)
        assert result.tzinfo == UTC

    def test_validate_date_invalid_string(self):
        """Test that invalid date strings raise ValueError."""
        with pytest.raises(ValueError, match="Invalid ISO date string"):
            validate_date_to_timestamp("not a date", "date")

    def test_validate_date_invalid_type(self):
        """Test that unsupported types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported date type"):
            validate_date_to_timestamp([], "date")


class TestValidationIntegration:
    """Integration tests for validation utilities."""

    def test_transaction_validation_flow(self):
        """Test typical transaction validation flow."""
        transaction = {
            "date_created": 1704067200,
            "amount": 99.99,
            "description": "Test transaction",
        }

        # Validate all fields
        date = require_field(transaction, "date_created", "transaction")
        amount = require_field(transaction, "amount", "transaction")
        description = require_field(transaction, "description", "transaction")

        # Convert and validate
        validated_timestamp = validate_posix_timestamp(date, "date_created")
        validated_amount = validate_amount(amount, "amount")

        assert validated_timestamp == 1704067200.0
        assert validated_amount == Decimal("99.99")
        assert description == "Test transaction"

    def test_missing_required_field_fails_fast(self):
        """Test that missing required fields fail immediately."""
        transaction = {
            "amount": 99.99,
            # Missing date_created
        }

        with pytest.raises(ValueError, match="Missing required field 'date_created'"):
            require_field(transaction, "date_created", "transaction")

    def test_invalid_amount_fails_fast(self):
        """Test that invalid amounts fail immediately."""
        transaction = {
            "date_created": 1704067200,
            "amount": "not a number",
        }

        amount = require_field(transaction, "amount", "transaction")
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount(amount, "amount")
