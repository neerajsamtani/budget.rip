from clients import splitwise_client
from constants import LIMIT, MOVING_DATE, PARTIES_TO_IGNORE, USER_FIRST_NAME
from dao import (
    get_all_data,
    line_items_collection,
    splitwise_raw_data_collection,
    upsert,
)
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from helpers import flip_amount, iso_8601_to_posix
from resources.line_item import LineItem

splitwise_blueprint = Blueprint("splitwise", __name__)


# TODO: Exceptions
# TODO: Can I remove MOVING_DATE_POSIX
# TODO: Can I remove PARTIES_TO_IGNORE

# TODO: Integrate with Splitwise OAuth to enable other people to use this without submitting API Keys
# https://blog.splitwise.com/2013/07/15/setting-up-oauth-for-the-splitwise-api/


@splitwise_blueprint.route("/api/refresh/splitwise")
@jwt_required()
def refresh_splitwise_api():
    refresh_splitwise()
    splitwise_to_line_items()
    return jsonify("Refreshed Splitwise Connection")


def refresh_splitwise():
    expenses = splitwise_client.getExpenses(limit=LIMIT, dated_after=MOVING_DATE)
    for expense in expenses:
        # TODO: What if an expense is deleted? What if it's part of an event?
        # Should I send a notification?
        if expense.deleted_at is not None:
            continue
        upsert(splitwise_raw_data_collection, expense)


def splitwise_to_line_items():
    payment_method = "Splitwise"
    expenses = get_all_data(splitwise_raw_data_collection)
    for expense in expenses:
        responsible_party = ""
        # Get Person Name
        for user in expense["users"]:
            if user["first_name"] != USER_FIRST_NAME:
                # TODO: Set up comma separated list of responsible parties
                responsible_party += f'{user["first_name"]} '
        if responsible_party in PARTIES_TO_IGNORE:
            continue
        posix_date = iso_8601_to_posix(expense["date"])
        for user in expense["users"]:
            if user["first_name"] != USER_FIRST_NAME:
                continue
            line_item = LineItem(
                f'line_item_{expense["_id"]}',
                posix_date,
                responsible_party,
                payment_method,
                expense["description"],
                flip_amount(user["net_balance"]),
            )
            upsert(line_items_collection, line_item)
            break
