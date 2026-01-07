import logging
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required

from dao import cash_raw_data_collection, get_all_data
from helpers import html_date_to_posix
from models.database import SessionLocal
from models.sql_models import LineItem as LineItemModel
from models.sql_models import Transaction
from resources.line_item import LineItem
from utils.id_generator import generate_id
from utils.pg_bulk_ops import upsert_line_items, upsert_transactions

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

    upsert_transactions([transaction], source="cash")

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
            transaction["date"],
            transaction["person"],
            payment_method,
            transaction["description"],
            transaction["amount"],
            source_id=str(transaction["source_id"]),
        )
        all_line_items.append(line_item)

    # Bulk upsert all collected line items at once
    if all_line_items:
        upsert_line_items(all_line_items, source="cash")
        logger.info(f"Converted {len(all_line_items)} cash transactions to line items")
    else:
        logger.info("No cash transactions to convert to line items")


@cash_blueprint.route("/api/cash_transaction/<line_item_id>", methods=["DELETE"])
@jwt_required()
def delete_cash_transaction_api(line_item_id: str) -> tuple[Response, int]:
    """
    Delete a cash transaction by its line item ID.

    Validates that:
    1. The line item exists
    2. The line item is a cash payment method
    3. The line item is not assigned to any event
    """
    session = SessionLocal()
    try:
        # Query line item with payment method relationship
        line_item = (
            session.query(LineItemModel)
            .filter(LineItemModel.id == line_item_id)
            .first()
        )

        if not line_item:
            logger.warning(f"Delete attempt for non-existent line item: {line_item_id}")
            return jsonify({"error": "Line item not found"}), 404

        # Verify it's a cash payment method
        if line_item.payment_method.name != "Cash":
            logger.warning(
                f"Delete attempt for non-cash line item: {line_item_id} "
                f"(payment method: {line_item.payment_method.name})"
            )
            return jsonify({"error": "Only cash transactions can be deleted"}), 400

        # Check if line item is assigned to any event
        if line_item.events:
            logger.warning(
                f"Delete attempt for line item assigned to event: {line_item_id}"
            )
            return jsonify({"error": "Cannot delete: line item is assigned to an event"}), 400

        # Get the transaction ID before deleting
        transaction_id = line_item.transaction_id

        # Delete the transaction (CASCADE will delete the line item)
        transaction = session.query(Transaction).filter(Transaction.id == transaction_id).first()
        if transaction:
            session.delete(transaction)
            session.commit()
            logger.info(f"Deleted cash transaction: {transaction_id} (line item: {line_item_id})")
        else:
            # Shouldn't happen due to FK constraint, but handle gracefully
            logger.error(f"Transaction not found for line item: {line_item_id}")
            return jsonify({"error": "Transaction not found"}), 404

        return jsonify({"message": "Deleted cash transaction"}), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting cash transaction: {e}")
        return jsonify({"error": "Failed to delete cash transaction"}), 500
    finally:
        session.close()
