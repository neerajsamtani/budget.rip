from datetime import datetime, timedelta
from typing import List, Dict
from venmo_api import Client
from line_item import LineItem
import json

def empty_list():
    return []

def to_dict(obj) -> Dict:
    return json.loads(json.dumps(obj, default=lambda o: o.__dict__))

def iso_8601_to_readable(date: str) -> str:
    date_time_obj = datetime.fromisoformat(date[:10])
    return date_time_obj.strftime("%b %d %Y")

def html_date_to_posix(date: str):
    date_time_obj = datetime.strptime(date, '%Y-%m-%d')
    return date_time_obj.timestamp()

def posix_to_readable(date: float) -> str:
    date_time_obj = datetime.fromtimestamp(date)
    return date_time_obj.strftime("%b %d %Y")

def iso_8601_to_posix(date: str) -> float:
    # TODO: Figure out a cleaner way to deal with timestamps
    # fromisoformat doesn't work with full date_string in python 8
    date_time_obj = datetime.fromisoformat(date[:10])
    return date_time_obj.timestamp()

def sort_by_date(line_items: List[LineItem]) -> List[LineItem]:
    """
    This function assumes that the line items contain the
    date at index 0
    """
    line_items.sort(reverse=True, key= lambda line_item : line_item["date"])
    return line_items

def convert_to_readable(line_items: List[LineItem]) -> List[LineItem]:
    """
    Make a line item readable
    """
    for line_item in line_items:
        # convert date
        line_item[0] = posix_to_readable(line_item[0])
    return line_items

def get_venmo_access_token(venmo_username: str, venmo_password: str) -> str:
    """
    This function triggers 2FA and requires interaction
    in the command line
    """
    return Client.get_access_token(username=venmo_username,
                                        password=venmo_password)

def flip_amount(amount: float) -> float:
    return -1 * float(amount)

def get_month_date_range(month_name = "February", year = "2023"):
    start_date = datetime.strptime(f"{month_name} {year}", '%B %Y')
    next_month = start_date.replace(day=28) + timedelta(days=4)
    end_date = next_month - timedelta(days=next_month.day) + timedelta(hours=23, minutes=59, seconds=59)
    return (start_date.timestamp(), end_date.timestamp())
