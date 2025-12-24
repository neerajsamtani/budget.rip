"""TypedDict definitions for event data."""

from typing import TypedDict, NotRequired


class EventDict(TypedDict):
    """Event grouping multiple line items.

    Events represent higher-level groupings like trips, shared expenses, etc.
    """
    id: str
    date: float  # POSIX timestamp
    name: str
    category: str
    amount: float
    line_items: list[str]
    tags: NotRequired[list[str]]
    is_duplicate_transaction: NotRequired[bool]
