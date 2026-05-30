import json
import re
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, TypeVar, Union

from apiflask import abort
from flask_bcrypt import check_password_hash, generate_password_hash
from venmo_api import Client

T = TypeVar("T")


def get_or_404(result: T | None, message: str = "Not found") -> T:
    if result is None:
        abort(404, message=message)
    return result  # type: ignore[return-value]


VenmoClient = Client


def empty_list() -> List[Any]:
    return []


def flip_amount(amount: float) -> float:
    return -1 * float(amount)


def cents_to_dollars(amount: float) -> float:
    return 0.01 * round(float(amount), 2)


def format_money(amount: Decimal) -> str:
    return str(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def to_dict(obj: Any) -> Dict[str, Any]:
    return json.loads(json.dumps(obj, default=lambda o: o.__dict__))


def to_dict_robust(obj: Any) -> Dict[str, Any]:
    """
    More robust version of to_dict that handles complex objects better.
    Falls back to the original to_dict if the robust version fails.
    """
    try:
        if isinstance(obj, dict):
            return obj
        elif hasattr(obj, "__dict__"):
            # For objects with __dict__ attribute
            return json.loads(json.dumps(obj, default=lambda o: o.__dict__))
        elif hasattr(obj, "__slots__"):
            # For objects with __slots__ (like some API objects)
            return {slot: getattr(obj, slot, None) for slot in obj.__slots__}
        else:
            # Fallback: try to convert to string and back
            return json.loads(json.dumps(obj, default=str))
    except Exception:
        # Final fallback to original to_dict
        return to_dict(obj)


def str_to_bool(value: Union[str, bool, None]) -> bool:
    """Convert string to boolean."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if value.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif value.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise ValueError(f'Cannot convert "{value}" to boolean')


def html_date_to_posix(date: str) -> float:
    date_time_obj: datetime = datetime.strptime(date, "%Y-%m-%d")
    date_time_obj = date_time_obj.replace(tzinfo=timezone.utc)
    return date_time_obj.timestamp()


def iso_8601_to_posix(date: str) -> float:
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}", date):
            dt = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
            return dt.timestamp()
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", date):
            dt = datetime.strptime(date[:-1], "%Y-%m-%dT%H:%M:%S")
            dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        else:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid ISO 8601 format") from exc


def sort_by_date_description(line_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Input a list of dictionaries representing LineItems (not actual LineItem objects)
    """
    line_items.sort(
        key=lambda line_item: (
            -datetime.fromtimestamp(line_item["date"], timezone.utc).date().toordinal(),
            line_item["description"].casefold(),
        )
    )
    return line_items


def get_venmo_access_token(venmo_username: str, venmo_password: str, venmo_client: Any = VenmoClient) -> str:
    """
    This function triggers 2FA and requires interaction
    in the command line
    """
    return venmo_client.get_access_token(username=venmo_username, password=venmo_password)


def hash_password(password: str) -> str:
    return generate_password_hash(password).decode("utf8")


def check_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)
