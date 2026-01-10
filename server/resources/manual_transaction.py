import logging
from typing import Any, Dict

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required

from helpers import html_date_to_posix
from utils.id_generator import generate_id
from utils.pg_bulk_ops import upsert_line_items, upsert_transactions

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
    from models.database import SessionLocal
    from models.sql_models import PaymentMethod
    from resources.line_item import LineItem

    data: Dict[str, Any] = request.get_json()

    # Validate required fields
    required_fields = ["date", "person", "description", "amount", "payment_method_id"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logger.warning(f"Manual transaction creation attempt missing required fields: {missing_fields}")
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    # Validate payment method exists
    db = SessionLocal()
    try:
        payment_method = db.query(PaymentMethod).filter(PaymentMethod.id == data["payment_method_id"]).first()
        if not payment_method:
            logger.warning(f"Manual transaction creation attempt with invalid payment method: {data['payment_method_id']}")
            return jsonify({"error": f"Payment method not found: {data['payment_method_id']}"}), 400

        payment_method_name = payment_method.name
    finally:
        db.close()

    # Generate manual transaction ID
    manual_transaction_id = generate_id("mantxn")
    posix_date = html_date_to_posix(data["date"])

    # Create the raw transaction record with empty source_data (manual transactions have no imported data)
    transaction = {
        "id": manual_transaction_id,
        "date": posix_date,
        "person": data["person"],
        "description": data["description"],
        "amount": float(data["amount"]),
        "payment_method_id": data["payment_method_id"],
    }

    # upsert_transactions uses the "id" field as source_id for deduplication
    upsert_transactions([transaction], source="manual")

    # Create the line item
    line_item = LineItem(
        posix_date,
        data["person"],
        payment_method_name,
        data["description"],
        float(data["amount"]),
        source_id=manual_transaction_id,  # Links line item to transaction via source_id lookup
    )

    upsert_line_items([line_item], source="manual")

    desc = data["description"]
    logger.info(f"Manual transaction created: {desc} - ${data['amount']} ({payment_method_name})")
    return jsonify({"message": "Created Manual Transaction", "transaction_id": manual_transaction_id}), 201


@manual_transaction_blueprint.route("/api/manual_transaction/<transaction_id>", methods=["DELETE"])
@jwt_required()
def delete_manual_transaction_api(transaction_id: str) -> tuple[Response, int]:
    """
    Delete a manual transaction and its associated line items.

    Only transactions with source='manual' can be deleted.
    API-synced transactions cannot be deleted through this endpoint.

    Returns:
        204 on successful deletion
        400 if transaction is not manual
        404 if transaction not found
    """
    from models.database import SessionLocal
    from models.sql_models import EventLineItem, LineItem, Transaction

    db = SessionLocal()
    try:
        # Find the transaction by source_id (the ID returned during creation)
        transaction = (
            db.query(Transaction).filter(Transaction.source_id == transaction_id, Transaction.source == "manual").first()
        )

        if not transaction:
            logger.warning(f"Delete attempt for non-existent transaction: {transaction_id}")
            return jsonify({"error": f"Transaction not found: {transaction_id}"}), 404

        # Find associated line item
        line_item = db.query(LineItem).filter(LineItem.transaction_id == transaction.id).first()

        # Check if line item is assigned to an event
        if line_item:
            is_assigned = db.query(EventLineItem).filter(EventLineItem.line_item_id == line_item.id).first()
            if is_assigned:
                logger.warning(f"Delete blocked: transaction {transaction_id} has line item assigned to an event")
                return (
                    jsonify(
                        {
                            "error": "Cannot delete transaction with line item assigned to an event. "
                            "Remove the line item from the event first."
                        }
                    ),
                    400,
                )

        # Delete transaction (line item cascades due to foreign key)
        db.delete(transaction)
        db.commit()

        logger.info(f"Deleted manual transaction {transaction_id}")
        return jsonify({}), 204

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete manual transaction {transaction_id}: {e}")
        return jsonify({"error": "Failed to delete transaction"}), 500
    finally:
        db.close()
