import logging
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required

from dao import cash_raw_data_collection, get_all_data
from helpers import html_date_to_posix
from resources.line_item import LineItem
from utils.id_generator import generate_id
from utils.pg_bulk_ops import upsert_line_items, upsert_transactions
from utils.validation import require_field, validate_amount

logger = logging.getLogger(__name__)

cash_blueprint = Blueprint("cash", __name__)

# TODO: Exceptions


@cash_blueprint.route("/api/cash_transaction", methods=["POST"])
@jwt_required()
def create_cash_transaction_api() -> tuple[Response, int]:
    try:
        transaction: Dict[str, Any] = request.get_json()
        if not transaction:
            return jsonify({"error": "Request body is required"}), 400

        # Validate required fields using validation utilities
        date_value = require_field(transaction, "date", "cash transaction")
        amount_value = require_field(transaction, "amount", "cash transaction")

        # Convert and validate amount
        validated_amount = validate_amount(amount_value, "amount")

        transaction["id"] = generate_id("cash")
        transaction["date"] = html_date_to_posix(date_value)
        transaction["amount"] = float(validated_amount)

        upsert_transactions([transaction], source="cash")

        description = transaction.get("description", "No description")
        logger.info(f"Cash transaction created: {description} - ${transaction['amount']}")
        cash_to_line_items()
        return jsonify("Created Cash Transaction"), 201
    except ValueError as e:
        logger.warning(f"Cash transaction creation failed: {e}")
        return jsonify({"error": str(e)}), 400


def cash_to_line_items() -> None:
    """Convert cash transactions to line items with optimized database operations.

    Validates required fields and fails fast if data is malformed.

    Optimizations:
    1. Use bulk upsert operations instead of individual upserts
    2. Collect all line items before bulk upserting
    3. Improved performance for large datasets

    Raises:
        ValueError: If required transaction fields are missing or invalid
    """
    payment_method: str = "Cash"
    cash_raw_data: List[Dict[str, Any]] = get_all_data(cash_raw_data_collection)

    # Collect all line items for bulk upsert
    all_line_items: List[LineItem] = []

    for transaction in cash_raw_data:
        # Validate required fields
        date = require_field(transaction, "date", "cash transaction")
        person = require_field(transaction, "person", "cash transaction")
        description = require_field(transaction, "description", "cash transaction")
        amount = require_field(transaction, "amount", "cash transaction")
        source_id = require_field(transaction, "source_id", "cash transaction")

        line_item = LineItem(
            date,
            person,
            payment_method,
            description,
            amount,
            source_id=str(source_id),
        )
        all_line_items.append(line_item)

    # Bulk upsert all collected line items at once
    if all_line_items:
        upsert_line_items(all_line_items, source="cash")
        logger.info(f"Converted {len(all_line_items)} cash transactions to line items")
    else:
        logger.info("No cash transactions to convert to line items")
