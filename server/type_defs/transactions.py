"""TypedDict definitions for transaction data from various sources."""

from typing import TypedDict, NotRequired, Union, Any


class VenmoTransactionDict(TypedDict):
    """Venmo transaction data structure."""
    _id: str
    date_created: float  # POSIX timestamp
    amount: float
    note: str
    payment_type: str
    actor: dict[str, Any]
    target: dict[str, Any]


class SplitwiseTransactionDict(TypedDict):
    """Splitwise transaction data structure."""
    _id: str
    date: str  # ISO 8601 format
    description: str
    users: list[dict[str, Any]]
    category: NotRequired[dict[str, Any]]


class StripeTransactionDict(TypedDict):
    """Stripe transaction data structure."""
    _id: str
    transacted_at: float  # POSIX timestamp
    amount: int  # Amount in cents
    description: str
    account: str
    status: str


class CashTransactionDict(TypedDict):
    """Cash transaction data structure."""
    _id: str
    date: float  # POSIX timestamp
    amount: float
    description: str
    person: str


TransactionDict = Union[
    VenmoTransactionDict,
    SplitwiseTransactionDict,
    StripeTransactionDict,
    CashTransactionDict,
]
