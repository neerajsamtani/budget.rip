from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required

from dao import (
    bulk_upsert,
    cash_raw_data_collection,
    get_all_data,
    insert,
    line_items_collection,
)
from helpers import html_date_to_posix
from resources.line_item import LineItem

cash_blueprint = Blueprint("cash", __name__)

# TODO: Exceptions


@cash_blueprint.route("/api/cash_transaction", methods=["POST"])
@jwt_required()
def create_cash_transaction_api() -> tuple[Response, int]:
    transaction: Dict[str, Any] = request.get_json()
    transaction["date"] = html_date_to_posix(transaction["date"])
    transaction["amount"] = int(transaction["amount"])
    insert(cash_raw_data_collection, transaction)
    cash_to_line_items()
    return jsonify("Created Cash Transaction"), 201


def cash_to_line_items() -> None:
    """
    Convert cash transactions to line items with optimized database operations.

    Optimizations:
    1. Use bulk upsert operations instead of individual upserts
    2. Collect all line items before bulk upserting
    3. Improved performance for large datasets
    """
    payment_method: str = "Cash"
    cash_raw_data: List[Dict[str, Any]] = get_all_data(cash_raw_data_collection)

    # Collect all line items for bulk upsert
    all_line_items: List[LineItem] = []

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
