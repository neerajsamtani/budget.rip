"""TypedDict definitions for external API responses."""

from typing import TypedDict, NotRequired, Any


class StripeInactiveDetailsDict(TypedDict):
    """Stripe inactive status details."""
    action: str


class StripeStatusDetailsDict(TypedDict):
    """Stripe authorization status details."""
    inactive: NotRequired[StripeInactiveDetailsDict]


class StripeAuthorizationDict(TypedDict):
    """Stripe authorization data structure."""
    status_details: NotRequired[StripeStatusDetailsDict]


class StripeBalanceDict(TypedDict):
    """Stripe account balance structure."""
    current: int  # Amount in cents
    available: NotRequired[int]  # Amount in cents


class StripeAccountDict(TypedDict):
    """Stripe account data structure."""
    id: str
    name: str
    mask: NotRequired[str]
    subtype: NotRequired[str]
    balance: NotRequired[StripeBalanceDict]
    authorization: NotRequired[StripeAuthorizationDict]
