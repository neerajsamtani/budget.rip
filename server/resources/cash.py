from dao import (
    cash_raw_data_collection,
    get_all_data,
    insert,
    line_items_collection,
    upsert,
)
from flask import Blueprint, jsonify, request
from helpers import html_date_to_posix

from line_item_class import LineItem

cash = Blueprint("cash", __name__)

# TODO: Exceptions


@cash.route("/api/cash_transaction", methods=["POST"])
def create_cash_transaction():
    transaction = request.json
    transaction["date"] = html_date_to_posix(transaction["date"])
    transaction["amount"] = int(transaction["amount"])
    insert(cash_raw_data_collection, transaction)
    cash_to_line_items()
    return jsonify("Created Cash Transaction")


def cash_to_line_items():
    payment_method = "Cash"
    cash_raw_data = get_all_data(cash_raw_data_collection)
    for transaction in cash_raw_data:
        line_item = LineItem(
            f'line_item_{transaction["_id"]}',
            transaction["date"],
            transaction["person"],
            payment_method,
            transaction["description"],
            transaction["amount"],
        )
        upsert(line_items_collection, line_item)
