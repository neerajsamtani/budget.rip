"""TypedDict definitions for line item data."""

from typing import NotRequired, TypedDict


class LineItemDict(TypedDict):
    """Normalized line item structure.

    This represents the standardized format for financial transactions
    across all sources (Venmo, Stripe, Splitwise, Cash).
    """

    # Required fields
    date: float  # POSIX timestamp
    payment_method: str
    description: str
    amount: float

    # Optional fields
    id: NotRequired[str]
    responsible_party: NotRequired[str]
    notes: NotRequired[str | None]
    transaction_id: NotRequired[str]
