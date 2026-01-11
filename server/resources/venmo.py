import logging
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required
from venmo_api.models.user import User

from clients import get_venmo_client
from constants import MOVING_DATE_POSIX, PARTIES_TO_IGNORE, USER_FIRST_NAME
from dao import get_transactions
from helpers import flip_amount
from models.database import SessionLocal
from resources.line_item import LineItem
from utils.pg_bulk_ops import bulk_upsert_line_items, bulk_upsert_transactions

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
        with SessionLocal.begin() as db:
            bulk_upsert_transactions(db, all_transactions, source="venmo_api")
        logger.info(f"Refreshed {len(all_transactions)} Venmo transactions")
    else:
        logger.info("No new Venmo transactions to refresh")


def venmo_to_line_items() -> None:
    """
    Convert Venmo transactions to line items with optimized database operations.

    Optimizations:
    1. Use bulk upsert operations instead of individual upserts
    2. Collect all line items before bulk upserting
    3. Improved logic flow for better performance
    """
    payment_method: str = "Venmo"
    venmo_raw_data: List[Dict[str, Any]] = get_transactions("venmo_api", None)

    # Collect all line items for bulk upsert
    all_line_items: List[LineItem] = []

    for venmo_transaction in venmo_raw_data:
        posix_date: float = float(venmo_transaction["date_created"])

        if venmo_transaction["actor"]["first_name"] == USER_FIRST_NAME and venmo_transaction["payment_type"] == "pay":
            # current user paid money
            line_item = LineItem(
                posix_date,
                venmo_transaction["target"]["first_name"],
                payment_method,
                venmo_transaction["note"],
                venmo_transaction["amount"],
                source_id=str(venmo_transaction["source_id"]),
            )
        elif venmo_transaction["target"]["first_name"] == USER_FIRST_NAME and venmo_transaction["payment_type"] == "charge":
            # current user paid money
            line_item = LineItem(
                posix_date,
                venmo_transaction["actor"]["first_name"],
                payment_method,
                venmo_transaction["note"],
                venmo_transaction["amount"],
                source_id=str(venmo_transaction["source_id"]),
            )
        else:
            # current user gets money
            if venmo_transaction["target"]["first_name"] == USER_FIRST_NAME:
                other_name: str = venmo_transaction["actor"]["first_name"]
            else:
                other_name: str = venmo_transaction["target"]["first_name"]
            line_item = LineItem(
                posix_date,
                other_name,
                payment_method,
                venmo_transaction["note"],
                flip_amount(venmo_transaction["amount"]),
                source_id=str(venmo_transaction["source_id"]),
            )

        all_line_items.append(line_item)

    # Bulk upsert all collected line items at once
    if all_line_items:
        with SessionLocal.begin() as db:
            bulk_upsert_line_items(db, all_line_items, source="venmo_api")
        logger.info(f"Converted {len(all_line_items)} Venmo transactions to line items")
    else:
        logger.info("No Venmo transactions to convert to line items")
