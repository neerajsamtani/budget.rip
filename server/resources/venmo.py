import logging
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required
from venmo_api.models.user import User

from clients import get_venmo_client
from constants import MOVING_DATE_POSIX, PARTIES_TO_IGNORE, USER_FIRST_NAME
from dao import (
    bulk_upsert,
    get_all_data,
    line_items_collection,
    venmo_raw_data_collection,
)
from helpers import flip_amount
from models import LineItem

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
    logging.info("Refreshing Venmo Data")
    profile: User | None = get_venmo_client().my_profile()
    if profile is None:
        logging.error("Failed to get Venmo profile")
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
            elif (
                transaction.actor.first_name in PARTIES_TO_IGNORE
                or transaction.target.first_name in PARTIES_TO_IGNORE
            ):
                continue
            all_transactions.append(transaction)
        transactions = (
            transactions.get_next_page()
        )  # TODO: This might have one extra network call when we break out of the loop

    # Bulk upsert all collected transactions at once
    if all_transactions:
        bulk_upsert(venmo_raw_data_collection, all_transactions)
        logging.info(f"Refreshed {len(all_transactions)} Venmo transactions")
    else:
        logging.info("No new Venmo transactions to refresh")


def venmo_to_line_items() -> None:
    """
    Convert Venmo transactions to line items with optimized database operations.

    Optimizations:
    1. Use bulk upsert operations instead of individual upserts
    2. Collect all line items before bulk upserting
    3. Improved logic flow for better performance
    """
    payment_method: str = "Venmo"
    venmo_raw_data: List[Dict[str, Any]] = get_all_data(venmo_raw_data_collection)

    # Collect all line items for bulk upsert
    all_line_items: List[LineItem] = []

    for transaction in venmo_raw_data:
        posix_date: float = float(transaction["date_created"])

        if (
            transaction["actor"]["first_name"] == USER_FIRST_NAME
            and transaction["payment_type"] == "pay"
        ):
            # current user paid money
            line_item = LineItem(
                id=f'line_item_{transaction["_id"]}',
                date=posix_date,
                responsible_party=transaction["target"]["first_name"],
                payment_method=payment_method,
                description=transaction["note"],
                amount=transaction["amount"],
            )
        elif (
            transaction["target"]["first_name"] == USER_FIRST_NAME
            and transaction["payment_type"] == "charge"
        ):
            # current user paid money
            line_item = LineItem(
                id=f'line_item_{transaction["_id"]}',
                date=posix_date,
                responsible_party=transaction["actor"]["first_name"],
                payment_method=payment_method,
                description=transaction["note"],
                amount=transaction["amount"],
            )
        else:
            # current user gets money
            if transaction["target"]["first_name"] == USER_FIRST_NAME:
                other_name: str = transaction["actor"]["first_name"]
            else:
                other_name: str = transaction["target"]["first_name"]
            line_item = LineItem(
                id=f'line_item_{transaction["_id"]}',
                date=posix_date,
                responsible_party=other_name,
                payment_method=payment_method,
                description=transaction["note"],
                amount=flip_amount(transaction["amount"]),
            )

        all_line_items.append(line_item)

    # Bulk upsert all collected line items at once
    if all_line_items:
        bulk_upsert(line_items_collection, all_line_items)
        logging.info(
            f"Converted {len(all_line_items)} Venmo transactions to line items"
        )
    else:
        logging.info("No Venmo transactions to convert to line items")
