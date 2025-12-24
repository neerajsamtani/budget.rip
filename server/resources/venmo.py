import logging
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required
from venmo_api.models.user import User

from clients import get_venmo_client
from constants import MOVING_DATE_POSIX, PARTIES_TO_IGNORE, USER_FIRST_NAME
from dao import get_all_data, venmo_raw_data_collection
from helpers import flip_amount
from resources.line_item import LineItem
from utils.pg_bulk_ops import upsert_line_items, upsert_transactions
from utils.validation import require_field, validate_posix_timestamp

logger = logging.getLogger(__name__)

venmo_blueprint = Blueprint("venmo", __name__)


# TODO: Exceptions
# TODO: Can I remove MOVING_DATE_POSIX
# TODO: Can I remove PARTIES_TO_IGNORE


@venmo_blueprint.route("/api/refresh/venmo")
@jwt_required()
def refresh_venmo_api() -> tuple[Response, int]:
    refresh_venmo()
    venmo_to_line_items()
    return jsonify("Refreshed Venmo Connection"), 200


def refresh_venmo() -> None:
    logger.info("Refreshing Venmo Data")
    profile: User | None = get_venmo_client().my_profile()
    if profile is None:
        logger.error("Failed to get Venmo profile")
        raise Exception("Failed to get Venmo profile")
    my_id: int = profile.id
    transactions: Any = get_venmo_client().user.get_user_transactions(str(my_id))  # type: ignore
    transactions_after_moving_date: bool = True

    # Collect all transactions for bulk upsert
    all_transactions: List[Any] = []

    while transactions and transactions_after_moving_date:
        for transaction in transactions:
            if transaction.date_created < MOVING_DATE_POSIX:
                transactions_after_moving_date = False
                break
            elif transaction.actor.first_name in PARTIES_TO_IGNORE or transaction.target.first_name in PARTIES_TO_IGNORE:
                continue
            all_transactions.append(transaction)
        transactions = (
            transactions.get_next_page()
        )  # TODO: This might have one extra network call when we break out of the loop

    # Bulk upsert all collected transactions at once
    if all_transactions:
        upsert_transactions(all_transactions, source="venmo")
        logger.info(f"Refreshed {len(all_transactions)} Venmo transactions")
    else:
        logger.info("No new Venmo transactions to refresh")


def venmo_to_line_items() -> None:
    """Convert Venmo transactions to line items with optimized database operations.

    Validates required fields and fails fast if data is malformed.

    Optimizations:
    1. Use bulk upsert operations instead of individual upserts
    2. Collect all line items before bulk upserting
    3. Improved logic flow for better performance

    Raises:
        ValueError: If required transaction fields are missing or invalid
    """
    payment_method: str = "Venmo"
    venmo_raw_data: List[Dict[str, Any]] = get_all_data(venmo_raw_data_collection)

    # Collect all line items for bulk upsert
    all_line_items: List[LineItem] = []

    for venmo_transaction in venmo_raw_data:
        # Validate required fields
        date_created = require_field(venmo_transaction, "date_created", "Venmo transaction")
        posix_date = validate_posix_timestamp(date_created, "date_created")

        actor = require_field(venmo_transaction, "actor", "Venmo transaction")
        target = require_field(venmo_transaction, "target", "Venmo transaction")
        actor_first_name = require_field(actor, "first_name", "Venmo actor")
        target_first_name = require_field(target, "first_name", "Venmo target")

        payment_type = require_field(venmo_transaction, "payment_type", "Venmo transaction")
        note = require_field(venmo_transaction, "note", "Venmo transaction")
        amount = require_field(venmo_transaction, "amount", "Venmo transaction")
        source_id = require_field(venmo_transaction, "source_id", "Venmo transaction")

        if actor_first_name == USER_FIRST_NAME and payment_type == "pay":
            # current user paid money
            line_item = LineItem(
                posix_date,
                target_first_name,
                payment_method,
                note,
                amount,
                source_id=str(source_id),
            )
        elif target_first_name == USER_FIRST_NAME and payment_type == "charge":
            # current user paid money
            line_item = LineItem(
                posix_date,
                actor_first_name,
                payment_method,
                note,
                amount,
                source_id=str(source_id),
            )
        else:
            # current user gets money
            if target_first_name == USER_FIRST_NAME:
                other_name = actor_first_name
            else:
                other_name = target_first_name
            line_item = LineItem(
                posix_date,
                other_name,
                payment_method,
                note,
                flip_amount(amount),
                source_id=str(source_id),
            )

        all_line_items.append(line_item)

    # Bulk upsert all collected line items at once
    if all_line_items:
        upsert_line_items(all_line_items, source="venmo")
        logger.info(f"Converted {len(all_line_items)} Venmo transactions to line items")
    else:
        logger.info("No Venmo transactions to convert to line items")
