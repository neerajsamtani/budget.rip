import logging
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required

from clients import splitwise_client
from constants import LIMIT, MOVING_DATE, PARTIES_TO_IGNORE, USER_FIRST_NAME
from dao import (
    bulk_upsert,
    get_all_data,
    line_items_collection,
    splitwise_raw_data_collection,
)
from helpers import flip_amount, iso_8601_to_posix
from resources.line_item import LineItem
from utils.dual_write import dual_write_operation
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
        dual_write_operation(
            mongo_write_func=lambda: bulk_upsert(splitwise_raw_data_collection, all_expenses),
            pg_write_func=lambda db: bulk_upsert_transactions(db, all_expenses, source="splitwise"),
            operation_name="splitwise_refresh_transactions",
        )
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
    expenses: List[Dict[str, Any]] = get_all_data(splitwise_raw_data_collection)

    # Collect all line items for bulk upsert
    all_line_items: List[LineItem] = []
    ignored_count = 0

    for expense in expenses:
        # Determine responsible party
        responsible_party: str = ""
        for user in expense["users"]:
            if user["first_name"] != USER_FIRST_NAME:
                # TODO: Set up comma separated list of responsible parties
                responsible_party += f"{user['first_name']} "

        # Skip if responsible party is in ignore list
        if responsible_party.strip() in PARTIES_TO_IGNORE:
            ignored_count += 1
            continue

        posix_date: float = iso_8601_to_posix(expense["date"])

        # Find the current user's data and create line item
        for user in expense["users"]:
            if user["first_name"] != USER_FIRST_NAME:
                continue

            line_item = LineItem(
                f"line_item_{expense['_id']}",
                posix_date,
                responsible_party,
                payment_method,
                expense["description"],
                flip_amount(user["net_balance"]),
            )
            all_line_items.append(line_item)
            break  # Found the user, no need to continue loop

    # Bulk upsert all collected line items at once
    if all_line_items:
        dual_write_operation(
            mongo_write_func=lambda: bulk_upsert(line_items_collection, all_line_items),
            pg_write_func=lambda db: bulk_upsert_line_items(db, all_line_items, source="splitwise"),
            operation_name="splitwise_create_line_items",
        )
        logger.info(f"Converted {len(all_line_items)} Splitwise expenses to line items (ignored {ignored_count})")
    else:
        logger.info("No Splitwise expenses to convert to line items")
