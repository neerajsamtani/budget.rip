from clients import venmo_client
from constants import MOVING_DATE_POSIX, PARTIES_TO_IGNORE, USER_FIRST_NAME
from dao import get_all_data, line_items_collection, upsert, venmo_raw_data_collection
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from helpers import flip_amount
from resources.line_item import LineItem

venmo_blueprint = Blueprint("venmo", __name__)


# TODO: Exceptions
# TODO: Can I remove MOVING_DATE_POSIX
# TODO: Can I remove PARTIES_TO_IGNORE


@venmo_blueprint.route("/api/refresh/venmo")
@jwt_required()
def refresh_venmo_api():
    refresh_venmo()
    venmo_to_line_items()
    return jsonify("Refreshed Venmo Connection")


def refresh_venmo():
    my_id = venmo_client.my_profile().id
    transactions = venmo_client.user.get_user_transactions(my_id)
    transactions_after_moving_date = True
    while transactions and transactions_after_moving_date:
        for transaction in transactions:
            if transaction.date_created < MOVING_DATE_POSIX:
                transactions_after_moving_date = False
                break
            elif (
                transaction.actor.first_name in PARTIES_TO_IGNORE
                or transaction.target.first_name in PARTIES_TO_IGNORE
            ):
                continue
            upsert(venmo_raw_data_collection, transaction)
        transactions = (
            transactions.get_next_page()
        )  # TODO: This might have one extra network call when we break out of the loop


def venmo_to_line_items():
    payment_method = "Venmo"
    venmo_raw_data = get_all_data(venmo_raw_data_collection)
    for transaction in venmo_raw_data:
        posix_date = float(transaction["date_created"])
        if (
            transaction["actor"]["first_name"] == USER_FIRST_NAME
            and transaction["payment_type"] == "pay"
        ):
            # current user paid money
            line_item = LineItem(
                f'line_item_{transaction["_id"]}',
                posix_date,
                transaction["target"]["first_name"],
                payment_method,
                transaction["note"],
                transaction["amount"],
            )
        elif (
            transaction["target"]["first_name"] == USER_FIRST_NAME
            and transaction["payment_type"] == "charge"
        ):
            # current user paid money
            line_item = LineItem(
                f'line_item_{transaction["_id"]}',
                posix_date,
                transaction["actor"]["first_name"],
                payment_method,
                transaction["note"],
                transaction["amount"],
            )
        else:
            # current user gets money
            if transaction["target"]["first_name"] == USER_FIRST_NAME:
                other_name = transaction["actor"]["first_name"]
            else:
                other_name = transaction["target"]["first_name"]
            line_item = LineItem(
                f'line_item_{transaction["_id"]}',
                posix_date,
                other_name,
                payment_method,
                transaction["note"],
                flip_amount(transaction["amount"]),
            )
        upsert(line_items_collection, line_item)
