import logging
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required

from clients import splitwise_client
from constants import LIMIT, MOVING_DATE, PARTIES_TO_IGNORE, USER_FIRST_NAME
from dao import get_transactions
from helpers import flip_amount, iso_8601_to_posix
from models.database import SessionLocal
from resources.line_item import LineItem
from utils.pg_bulk_ops import bulk_upsert_line_items, bulk_upsert_transactions

logger = logging.getLogger(__name__)

splitwise_blueprint = Blueprint("splitwise", __name__)


# TODO: Exceptions
# TODO: Can I remove MOVING_DATE_POSIX
# TODO: Can I remove PARTIES_TO_IGNORE

# TODO: Integrate with Splitwise OAuth to enable other people to use this without submitting API Keys
# https://blog.splitwise.com/2013/07/15/setting-up-oauth-for-the-splitwise-api/


@splitwise_blueprint.route("/api/refresh/splitwise")
@jwt_required()
def refresh_splitwise_api() -> tuple[Response, int]:
    refresh_splitwise()
    splitwise_to_line_items()
    return jsonify("Refreshed Splitwise Connection"), 200


def refresh_splitwise() -> None:
    logger.info("Refreshing Splitwise Data")
    expenses: List[Any] = splitwise_client.getExpenses(limit=LIMIT, dated_after=MOVING_DATE)

    # Collect all non-deleted expenses for bulk upsert
    all_expenses: List[Any] = []
    deleted_count = 0
    for expense in expenses:
        # TODO: What if an expense is deleted? What if it's part of an event?
        # Should I send a notification?
        if expense.deleted_at is not None:
            deleted_count += 1
            continue
        all_expenses.append(expense)

    # Bulk upsert all collected expenses at once
    if all_expenses:
        with SessionLocal.begin() as db:
            bulk_upsert_transactions(db, all_expenses, source="splitwise_api")
        logger.info(f"Refreshed {len(all_expenses)} Splitwise expenses (skipped {deleted_count} deleted)")
    else:
        logger.info("No new Splitwise expenses to refresh")


def splitwise_to_line_items() -> None:
    """
    Convert Splitwise expenses to line items with optimized database operations.

    Optimizations:
    1. Use bulk upsert operations instead of individual upserts
    2. Collect all line items before bulk upserting
    3. Improved logic flow for better performance
    """
    payment_method: str = "Splitwise"
    splitwise_raw_data: List[Dict[str, Any]] = get_transactions("splitwise_api", None)

    # Collect all line items for bulk upsert
    all_line_items: List[LineItem] = []
    ignored_count = 0

    for splitwise_transaction in splitwise_raw_data:
        # Determine responsible party
        responsible_party: str = ""
        for user in splitwise_transaction["users"]:
            if user["first_name"] != USER_FIRST_NAME:
                # TODO: Set up comma separated list of responsible parties
                responsible_party += f"{user['first_name']} "

        # Skip if responsible party is in ignore list
        if responsible_party.strip() in PARTIES_TO_IGNORE:
            ignored_count += 1
            continue

        posix_date: float = iso_8601_to_posix(splitwise_transaction["date"])

        # Find the current user's data and create line item
        for user in splitwise_transaction["users"]:
            if user["first_name"] != USER_FIRST_NAME:
                continue

            line_item = LineItem(
                posix_date,
                responsible_party,
                payment_method,
                splitwise_transaction["description"],
                flip_amount(user["net_balance"]),
                source_id=str(splitwise_transaction["source_id"]),
            )
            all_line_items.append(line_item)
            break  # Found the user, no need to continue loop

    # Bulk upsert all collected line items at once
    if all_line_items:
        with SessionLocal.begin() as db:
            bulk_upsert_line_items(db, all_line_items, source="splitwise_api")
        logger.info(f"Converted {len(all_line_items)} Splitwise expenses to line items (ignored {ignored_count})")
    else:
        logger.info("No Splitwise expenses to convert to line items")
