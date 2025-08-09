import logging
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
from models import CashTransaction, LineItem

cash_blueprint = Blueprint("cash", __name__)

# TODO: Exceptions


@cash_blueprint.route("/api/cash_transaction", methods=["POST"])
@jwt_required()
def create_cash_transaction_api() -> tuple[Response, int]:
    body: Dict[str, Any] = request.get_json()
    transaction_model = CashTransaction(
        date=html_date_to_posix(body["date"]),
        person=body["person"],
        description=body["description"],
        amount=int(body["amount"]),
    )
    insert(cash_raw_data_collection, transaction_model)
    logging.info(
        f"Cash transaction created: {transaction_model.description} - ${transaction_model.amount}"
    )
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
            id=f'line_item_{transaction["_id"]}',
            date=transaction["date"],
            responsible_party=transaction["person"],
            payment_method=payment_method,
            description=transaction["description"],
            amount=transaction["amount"],
        )
        all_line_items.append(line_item)

    # Bulk upsert all collected line items at once
    if all_line_items:
        bulk_upsert(line_items_collection, all_line_items)
        logging.info(f"Converted {len(all_line_items)} cash transactions to line items")
    else:
        logging.info("No cash transactions to convert to line items")
