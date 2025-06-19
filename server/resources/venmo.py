from clients import venmo_client
from constants import MOVING_DATE_POSIX, PARTIES_TO_IGNORE, USER_FIRST_NAME
from dao import (
    bulk_upsert,
    get_all_data,
    line_items_collection,
    venmo_raw_data_collection,
)
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
    print("Refreshing Venmo Data")
    my_id = venmo_client.my_profile().id
    transactions = venmo_client.user.get_user_transactions(my_id)
    transactions_after_moving_date = True

    # Collect all transactions for bulk upsert
    all_transactions = []

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
            all_transactions.append(transaction)
        transactions = (
            transactions.get_next_page()
        )  # TODO: This might have one extra network call when we break out of the loop

    # Bulk upsert all collected transactions at once
    if all_transactions:
        bulk_upsert(venmo_raw_data_collection, all_transactions)


def venmo_to_line_items():
    """
    Convert Venmo transactions to line items with optimized database operations.

    Optimizations:
    1. Use bulk upsert operations instead of individual upserts
    2. Collect all line items before bulk upserting
    3. Improved logic flow for better performance
    """
    payment_method = "Venmo"
    venmo_raw_data = get_all_data(venmo_raw_data_collection)

    # Collect all line items for bulk upsert
    all_line_items = []

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

        all_line_items.append(line_item)

    # Bulk upsert all collected line items at once
    if all_line_items:
        bulk_upsert(line_items_collection, all_line_items)
