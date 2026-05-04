import logging
from datetime import UTC, datetime
from decimal import Decimal

from apiflask import APIBlueprint, abort
from flask_jwt_extended import jwt_required

from dao import create_manual_transaction, delete_manual_transaction, get_payment_method_by_id
from helpers import html_date_to_posix
from resources.schemas.manual_transaction import (
    ErrorResponse,
    ManualTransactionCreateIn,
    ManualTransactionCreateResponse,
    MessageResponse,
)
from utils.id_generator import generate_id

logger = logging.getLogger(__name__)

manual_transaction_blueprint = APIBlueprint("manual_transaction", __name__)

_SECURITY = [{"jwtCookie": []}]
_ERROR_RESPONSES = {
    400: {"description": "Bad request", "schema": ErrorResponse},
    404: {"description": "Not found", "schema": ErrorResponse},
}


@manual_transaction_blueprint.post("/api/manual_transaction")
@manual_transaction_blueprint.input(ManualTransactionCreateIn, arg_name="body")
@manual_transaction_blueprint.output(ManualTransactionCreateResponse, status_code=201)
@manual_transaction_blueprint.doc(security=_SECURITY, responses=_ERROR_RESPONSES)
@jwt_required()
def create_manual_transaction_api(body: ManualTransactionCreateIn):
    """Create a manual transaction against any payment method."""
    payment_method = get_payment_method_by_id(body.payment_method_id)
    if not payment_method:
        logger.warning(f"Manual transaction creation attempt with invalid payment method: {body.payment_method_id}")
        abort(400, message=f"Payment method not found: {body.payment_method_id}")

    transaction_id = generate_id("txn")
    line_item_id = generate_id("li")
    posix_date = html_date_to_posix(body.date)
    transaction_date = datetime.fromtimestamp(posix_date, UTC)

    create_manual_transaction(
        transaction_id=transaction_id,
        line_item_id=line_item_id,
        transaction_date=transaction_date,
        posix_date=posix_date,
        amount=Decimal(str(body.amount)),
        description=body.description,
        payment_method_id=body.payment_method_id,
        responsible_party=body.person,
    )

    logger.info(f"Manual transaction created: {body.description} - ${body.amount} ({payment_method['name']})")
    return ManualTransactionCreateResponse(message="Created Manual Transaction", transaction_id=transaction_id), 201


@manual_transaction_blueprint.delete("/api/manual_transaction/<transaction_id>")
@manual_transaction_blueprint.output(MessageResponse, status_code=204)
@manual_transaction_blueprint.doc(security=_SECURITY, responses=_ERROR_RESPONSES)
@jwt_required()
def delete_manual_transaction_api(transaction_id: str):
    """Delete a manual transaction and its associated line items."""
    try:
        deleted = delete_manual_transaction(transaction_id)

        if not deleted:
            logger.warning(f"Delete attempt for non-existent transaction: {transaction_id}")
            abort(404, message=f"Transaction not found: {transaction_id}")

        logger.info(f"Deleted manual transaction {transaction_id}")
        return MessageResponse(message="Manual transaction deleted"), 204

    except ValueError as e:
        logger.warning(f"Delete blocked: transaction {transaction_id} - {e}")
        abort(
            400,
            message="Cannot delete transaction with line item assigned to an event. "
            "Remove the line item from the event first.",
        )
