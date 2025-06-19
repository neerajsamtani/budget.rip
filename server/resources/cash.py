from dao import (
    bulk_upsert,
    cash_raw_data_collection,
    get_all_data,
    insert,
    line_items_collection,
    upsert,
)
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from helpers import html_date_to_posix
from resources.line_item import LineItem

cash_blueprint = Blueprint("cash", __name__)

# TODO: Exceptions


@cash_blueprint.route("/api/cash_transaction", methods=["POST"])
@jwt_required()
def create_cash_transaction_api():
    transaction = request.get_json()
    transaction["date"] = html_date_to_posix(transaction["date"])
    transaction["amount"] = int(transaction["amount"])
    insert(cash_raw_data_collection, transaction)
    cash_to_line_items()
    return jsonify("Created Cash Transaction")


def cash_to_line_items():
    """
    Convert cash transactions to line items with optimized database operations.

    Optimizations:
    1. Use bulk upsert operations instead of individual upserts
    2. Collect all line items before bulk upserting
    3. Improved performance for large datasets
    """
    payment_method = "Cash"
    cash_raw_data = get_all_data(cash_raw_data_collection)

    # Collect all line items for bulk upsert
    all_line_items = []

    for transaction in cash_raw_data:
        line_item = LineItem(
            f'line_item_{transaction["_id"]}',
            transaction["date"],
            transaction["person"],
            payment_method,
            transaction["description"],
            transaction["amount"],
        )
        all_line_items.append(line_item)

    # Bulk upsert all collected line items at once
    if all_line_items:
        bulk_upsert(line_items_collection, all_line_items)
