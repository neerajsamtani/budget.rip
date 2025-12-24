"""Validation utilities for fail-fast data processing.

These utilities help enforce type safety and data integrity by validating
data structures early in the processing pipeline, preventing silent failures
in financial data processing.
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

logger = logging.getLogger(__name__)


def require_field(data: dict, field: str, context: str = "") -> Any:
    """Require a field to exist in a dictionary.

    Args:
        data: Dictionary to check
        field: Field name to require
        context: Optional context for error message

    Returns:
        The value of the required field

    Raises:
        ValueError: If the field is missing
    """
    if field not in data:
        available_fields = list(data.keys())
        context_str = f" in {context}" if context else ""
        raise ValueError(f"Missing required field '{field}'{context_str}. Available fields: {available_fields}")
    return data[field]


def validate_posix_timestamp(value: Any, field_name: str) -> float:
    """Validate and convert a value to a POSIX timestamp.

    Args:
        value: Value to validate (should be numeric)
        field_name: Field name for error messages

    Returns:
        Valid POSIX timestamp as float

    Raises:
        ValueError: If the value cannot be converted or is invalid
    """
    try:
        timestamp = float(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid timestamp for '{field_name}': {value} (type: {type(value).__name__})") from e

    if timestamp < 0:
        raise ValueError(f"Timestamp cannot be negative: {timestamp}")

    return timestamp


def validate_amount(value: Any, field_name: str) -> Decimal:
    """Validate and convert a value to a Decimal amount.

    Args:
        value: Value to validate (should be numeric)
        field_name: Field name for error messages

    Returns:
        Valid amount as Decimal

    Raises:
        ValueError: If the value cannot be converted to a decimal
    """
    try:
        amount = Decimal(str(value))
        return amount
    except (ValueError, TypeError, InvalidOperation) as e:
        raise ValueError(f"Invalid amount for '{field_name}': {value} (type: {type(value).__name__})") from e


def validate_date_to_timestamp(date_value: Any, field_name: str) -> datetime:
    """Validate and convert various date formats to datetime.

    Args:
        date_value: Date value (POSIX timestamp, datetime, or ISO string)
        field_name: Field name for error messages

    Returns:
        datetime object in UTC

    Raises:
        ValueError: If the date cannot be parsed
    """
    if isinstance(date_value, datetime):
        # Already a datetime, ensure UTC
        if date_value.tzinfo is None:
            return date_value.replace(tzinfo=UTC)
        return date_value.astimezone(UTC)

    if isinstance(date_value, (int, float)):
        # POSIX timestamp
        timestamp = validate_posix_timestamp(date_value, field_name)
        return datetime.fromtimestamp(timestamp, UTC)

    if isinstance(date_value, str):
        # ISO 8601 string
        try:
            dt = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=UTC)
            return dt.astimezone(UTC)
        except ValueError as e:
            raise ValueError(f"Invalid ISO date string for '{field_name}': {date_value}") from e

    raise ValueError(f"Unsupported date type for '{field_name}': {type(date_value).__name__}")
