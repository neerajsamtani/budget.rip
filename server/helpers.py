import json
import re
from datetime import datetime
from typing import Dict, List

from flask_bcrypt import check_password_hash, generate_password_hash
from venmo_api import Client

VenmoClient = Client


def empty_list():
    return []


def flip_amount(amount: float) -> float:
    return -1 * float(amount)


def cents_to_dollars(amount: float) -> float:
    return 0.01 * round(float(amount), 2)


def to_dict(obj) -> Dict:
    return json.loads(json.dumps(obj, default=lambda o: o.__dict__))


def to_dict_robust(obj) -> Dict:
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


def str_to_bool(value: str | bool | None) -> bool:
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


def iso_8601_to_readable(date: str) -> str:
    # TODO: Don't strip time data from date
    # Check that the input is a valid ISO 8601 date string with a time component.
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", date):
        raise ValueError(
            "Invalid input: string must be in ISO 8601 format with a time component."
        )
    date_time_obj = datetime.fromisoformat(date[:10])
    return date_time_obj.strftime("%b %d %Y")


def html_date_to_posix(date: str):
    date_time_obj = datetime.strptime(date, "%Y-%m-%d")
    return date_time_obj.timestamp()


def posix_to_readable(date: float) -> str:
    date_time_obj = datetime.fromtimestamp(date)
    return date_time_obj.strftime("%b %d %Y")


def iso_8601_to_posix(date: str) -> float:
    # TODO: Check if this handles timezones correctly
    posix_timestamp = -1
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}", date):
            dt = datetime.strptime(date[:-6], "%Y-%m-%dT%H:%M:%S")
            tz = datetime.strptime(date[-6:], "%z").utcoffset()
            posix_timestamp = (dt - tz).timestamp()
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", date):
            posix_timestamp = datetime.fromisoformat(date[:10]).timestamp()
        else:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid ISO 8601 format") from exc
    return posix_timestamp


def sort_by_date(line_items: List[Dict]) -> List[Dict]:
    """
    Input a list of dictionaries representing LineItems (not actual LineItem objects)
    """
    line_items.sort(reverse=True, key=lambda line_item: line_item["date"])
    return line_items


def get_venmo_access_token(
    venmo_username: str, venmo_password: str, venmo_client=VenmoClient
) -> str:
    """
    This function triggers 2FA and requires interaction
    in the command line
    """
    return venmo_client.get_access_token(
        username=venmo_username, password=venmo_password
    )


def hash_password(password: str) -> str:
    return generate_password_hash(password).decode("utf8")


def check_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)
