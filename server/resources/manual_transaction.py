import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Dict

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required

from dao import create_manual_transaction, delete_manual_transaction, get_payment_method_by_id
from helpers import html_date_to_posix
from utils.id_generator import generate_id

logger = logging.getLogger(__name__)

manual_transaction_blueprint = Blueprint("manual_transaction", __name__)


@manual_transaction_blueprint.route("/api/manual_transaction", methods=["POST"])
@jwt_required()
def create_manual_transaction_api() -> tuple[Response, int]:
    """
    Create a manual transaction against any payment method.

    Request body:
        date: str - Date in YYYY-MM-DD format
        person: str - Responsible party name
        description: str - Transaction description
        amount: float - Transaction amount
        payment_method_id: str - ID of the payment method (e.g., pm_xxx)

    Returns:
        201 on success
        400 if required fields are missing or payment method not found
    """
    data: Dict[str, Any] = request.get_json()

    # Validate required fields
    required_fields = ["date", "person", "description", "amount", "payment_method_id"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logger.warning(f"Manual transaction creation attempt missing required fields: {missing_fields}")
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    # Validate payment method exists
    payment_method = get_payment_method_by_id(data["payment_method_id"])
    if not payment_method:
        logger.warning(f"Manual transaction creation attempt with invalid payment method: {data['payment_method_id']}")
        return jsonify({"error": f"Payment method not found: {data['payment_method_id']}"}), 400

    # Generate IDs and prepare data
    transaction_id = generate_id("txn")
    line_item_id = generate_id("li")
    posix_date = html_date_to_posix(data["date"])
    transaction_date = datetime.fromtimestamp(posix_date, UTC)

    try:
        create_manual_transaction(
            transaction_id=transaction_id,
            line_item_id=line_item_id,
            transaction_date=transaction_date,
            posix_date=posix_date,
            amount=Decimal(str(data["amount"])),
            description=data["description"],
            payment_method_id=data["payment_method_id"],
            responsible_party=data["person"],
        )

        desc = data["description"]
        logger.info(f"Manual transaction created: {desc} - ${data['amount']} ({payment_method['name']})")
        return jsonify({"message": "Created Manual Transaction", "transaction_id": transaction_id}), 201

    except Exception as e:
        logger.error(f"Failed to create manual transaction: {e}")
        return jsonify({"error": "Failed to create transaction"}), 500


@manual_transaction_blueprint.route("/api/manual_transaction/<transaction_id>", methods=["DELETE"])
@jwt_required()
def delete_manual_transaction_api(transaction_id: str) -> tuple[Response, int]:
    """
    Delete a manual transaction and its associated line items.

    Only transactions with source='manual' can be deleted.
    API-synced transactions cannot be deleted through this endpoint.

    Returns:
        204 on successful deletion
        400 if transaction's line item is assigned to an event
        404 if transaction not found
    """
    try:
        deleted = delete_manual_transaction(transaction_id)

        if not deleted:
            logger.warning(f"Delete attempt for non-existent transaction: {transaction_id}")
            return jsonify({"error": f"Transaction not found: {transaction_id}"}), 404

        logger.info(f"Deleted manual transaction {transaction_id}")
        return jsonify({}), 204

    except ValueError as e:
        logger.warning(f"Delete blocked: transaction {transaction_id} - {e}")
        return (
            jsonify(
                {
                    "error": "Cannot delete transaction with line item assigned to an event. "
                    "Remove the line item from the event first."
                }
            ),
            400,
        )
    except Exception as e:
        logger.error(f"Failed to delete manual transaction {transaction_id}: {e}")
        return jsonify({"error": "Failed to delete transaction"}), 500
