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
from resources.line_item import LineItem
from utils.dual_write import dual_write_operation
from utils.id_generator import generate_id
from utils.pg_bulk_ops import bulk_upsert_line_items, bulk_upsert_transactions

logger = logging.getLogger(__name__)

cash_blueprint = Blueprint("cash", __name__)

# TODO: Exceptions


@cash_blueprint.route("/api/cash_transaction", methods=["POST"])
@jwt_required()
def create_cash_transaction_api() -> tuple[Response, int]:
    transaction: Dict[str, Any] = request.get_json()

    # Validate required fields
    required_fields = ["date", "amount"]
    missing_fields = [field for field in required_fields if field not in transaction]
    if missing_fields:
        logger.warning(f"Cash transaction creation attempt missing required fields: {missing_fields}")
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    transaction["id"] = generate_id("cash")
    transaction["date"] = html_date_to_posix(transaction["date"])
    transaction["amount"] = float(transaction["amount"])
    dual_write_operation(
        mongo_write_func=lambda: insert(cash_raw_data_collection, transaction),
        pg_write_func=lambda db: bulk_upsert_transactions(db, [transaction], source="cash"),
        operation_name="cash_create_transaction",
    )
    logger.info(f"Cash transaction created: {transaction['description']} - ${transaction['amount']}")
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
            f"line_item_{transaction['_id']}",
            transaction["date"],
            transaction["person"],
            payment_method,
            transaction["description"],
            transaction["amount"],
        )
        all_line_items.append(line_item)

    # Bulk upsert all collected line items at once
    if all_line_items:
        dual_write_operation(
            mongo_write_func=lambda: bulk_upsert(line_items_collection, all_line_items),
            pg_write_func=lambda db: bulk_upsert_line_items(db, all_line_items, source="cash"),
            operation_name="cash_create_line_items",
        )
        logger.info(f"Converted {len(all_line_items)} cash transactions to line items")
    else:
        logger.info("No cash transactions to convert to line items")
