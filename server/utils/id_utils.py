"""Utility functions for ID format detection and handling."""


def is_postgres_id(id: str, prefix: str) -> bool:
    """
    Check if an ID follows the PostgreSQL format (prefix_xxx).

    PostgreSQL IDs use a prefix followed by underscore (e.g., "evt_01K...", "li_001").
    MongoDB IDs typically follow different patterns (e.g., "event_cash_...", "event{hash}",
    or ObjectId hex strings like "507f1f77bcf86cd799439011").

    Args:
        id: The ID string to check
        prefix: The expected prefix (e.g., "evt", "li", "user")

    Returns:
        True if the ID starts with the expected prefix pattern
    """
    return id.startswith(f"{prefix}_")
