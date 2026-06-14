import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from apiflask import APIBlueprint, abort
from flask import Response, jsonify
from flask_jwt_extended import jwt_required
from splitwise.expense import Expense
from splitwise.user import ExpenseUser

from clients import splitwise_client
from constants import LIMIT, MOVING_DATE, PARTIES_TO_IGNORE, USER_FIRST_NAME
from dao import get_transactions
from helpers import flip_amount, format_money, iso_8601_to_posix
from models.database import SessionLocal
from resources.line_item import LineItem
from resources.schemas.splitwise import (
    SplitwiseCurrentUserResponse,
    SplitwiseErrorResponse,
    SplitwiseExpenseCreateIn,
    SplitwiseExpenseCreateResponse,
    SplitwiseFriendListResponse,
)
from utils.pg_bulk_ops import (
    bulk_upsert_line_items,
    bulk_upsert_transactions,
    delete_transactions_for_removed_sources,
)

logger = logging.getLogger(__name__)

splitwise_blueprint = APIBlueprint("splitwise", __name__)
_SECURITY = [{"jwtCookie": []}]
_ERROR_RESPONSES = {
    400: {"description": "Bad request", "schema": SplitwiseErrorResponse},
}


# TODO: Can I remove MOVING_DATE_POSIX
# TODO: Can I remove PARTIES_TO_IGNORE

# TODO: Integrate with Splitwise OAuth to enable other people to use this without submitting API Keys
# https://blog.splitwise.com/2013/07/15/setting-up-oauth-for-the-splitwise-api/


@splitwise_blueprint.route("/api/refresh/splitwise")
@jwt_required()
def refresh_splitwise_api() -> tuple[Response, int]:
    try:
        refresh_splitwise()
        splitwise_to_line_items()
        return jsonify("Refreshed Splitwise Connection"), 200
    except Exception as e:
        logger.error(f"Splitwise refresh failed: {e}", exc_info=True)
        return jsonify({"error": "Splitwise refresh failed"}), 500


@splitwise_blueprint.get("/api/splitwise/friends")
@splitwise_blueprint.output(SplitwiseFriendListResponse)
@splitwise_blueprint.doc(security=_SECURITY)
@jwt_required()
def get_splitwise_friends_api():
    """Get Splitwise friends for expense creation."""
    try:
        return SplitwiseFriendListResponse(data=list_splitwise_friends(splitwise_client))
    except Exception as e:
        logger.error(f"Failed to fetch Splitwise friends: {e}", exc_info=True)
        abort(503, message="Failed to fetch Splitwise friends")


@splitwise_blueprint.get("/api/splitwise/current-user")
@splitwise_blueprint.output(SplitwiseCurrentUserResponse)
@splitwise_blueprint.doc(security=_SECURITY)
@jwt_required()
def get_splitwise_current_user_api():
    """Get the authenticated Splitwise user."""
    try:
        return SplitwiseCurrentUserResponse(data={"id": splitwise_client.getCurrentUser().getId()})
    except Exception as e:
        logger.error(f"Failed to fetch Splitwise current user: {e}", exc_info=True)
        abort(503, message="Failed to fetch Splitwise current user")


@splitwise_blueprint.post("/api/splitwise/expenses")
@splitwise_blueprint.input(SplitwiseExpenseCreateIn, arg_name="body")
@splitwise_blueprint.output(SplitwiseExpenseCreateResponse, status_code=201)
@splitwise_blueprint.doc(security=_SECURITY, responses=_ERROR_RESPONSES)
@jwt_required()
def create_splitwise_expense_api(body: SplitwiseExpenseCreateIn):
    """Create a Splitwise expense."""
    try:
        created_expense, errors = create_splitwise_expense(splitwise_client, body.model_dump())
    except ValueError as exc:
        abort(400, message=str(exc))
    except Exception as e:
        logger.error(f"Splitwise expense creation failed: {e}", exc_info=True)
        abort(503, message="Failed to create Splitwise expense")

    if errors:
        logger.warning(f"Splitwise expense creation failed: {errors.getErrors()}")
        abort(400, message="Failed to create Splitwise expense", detail=errors.getErrors())

    # TODO: Consider a targeted refresh/import path so created Splitwise expenses can appear immediately without
    # making this endpoint responsible for the broader refresh flow.

    return SplitwiseExpenseCreateResponse(
        message="Created Splitwise Expense",
        data={
            "id": created_expense.getId() if created_expense else None,
            "description": created_expense.getDescription() if created_expense else body.description,
        },
    )


def list_splitwise_friends(client) -> List[Dict[str, Any]]:
    friends = [serialize_splitwise_friend(friend) for friend in client.getFriends()]
    return sorted(friends, key=lambda friend: friend["name"].lower())


def serialize_splitwise_friend(friend) -> Dict[str, Any]:
    first_name = title_case_name(friend.getFirstName())
    last_name = title_case_name(friend.getLastName())
    return {
        "id": friend.getId(),
        "first_name": first_name,
        "last_name": last_name,
        "name": f"{first_name} {last_name}".strip(),
        "email": friend.getEmail(),
    }


def title_case_name(name: str | None) -> str:
    return (name or "").title()


def create_splitwise_expense(client, data: Dict[str, Any]):
    description = str(data.get("description", "")).strip()
    friend_ids = data.get("friend_ids", [])
    amount = parse_splitwise_amount(data.get("amount"), "amount")

    if not description:
        raise ValueError("description is required")
    if amount <= 0:
        raise ValueError("amount must be greater than 0")
    if not isinstance(friend_ids, list) or len(friend_ids) == 0:
        raise ValueError("friend_ids must include at least one Splitwise friend")

    try:
        splitwise_friend_ids = [int(friend_id) for friend_id in friend_ids]
    except (TypeError, ValueError) as exc:
        raise ValueError("friend_ids must be Splitwise user IDs") from exc
    if len(set(splitwise_friend_ids)) != len(splitwise_friend_ids):
        raise ValueError("friend_ids must not contain duplicates")

    current_user = client.getCurrentUser()
    current_user_id = current_user.getId()
    participant_ids = [current_user_id, *splitwise_friend_ids]
    if len(set(participant_ids)) != len(participant_ids):
        raise ValueError("friend_ids must not contain the current Splitwise user")

    split_method = data.get("split_method", "equal")
    owed_shares = (
        build_equal_owed_shares(amount, participant_ids)
        if split_method == "equal"
        else parse_custom_owed_shares(data.get("owed_shares"), amount, participant_ids)
    )
    expense = build_splitwise_expense(
        amount=amount,
        description=description,
        current_user_id=current_user_id,
        owed_shares=owed_shares,
        currency_code=data.get("currency_code", "USD"),
        date=data.get("date"),
    )
    return client.createExpense(expense)


def parse_splitwise_amount(value: Any, field_name: str) -> Decimal:
    try:
        amount = Decimal(str(value))
        normalized_amount = Decimal(format_money(amount))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid monetary amount") from exc
    if not amount.is_finite() or amount < 0 or amount != normalized_amount:
        raise ValueError(f"{field_name} must be a non-negative monetary amount with at most two decimal places")
    return normalized_amount


def parse_custom_owed_shares(
    owed_shares: Any,
    amount: Decimal,
    participant_ids: List[int],
) -> Dict[int, Decimal]:
    if not isinstance(owed_shares, dict):
        raise ValueError("owed_shares must include exactly one amount for every participant")

    parsed_shares: Dict[int, Decimal] = {}
    try:
        for user_id, share in owed_shares.items():
            parsed_user_id = int(user_id)
            if parsed_user_id in parsed_shares:
                raise ValueError("owed_shares must include exactly one amount for every participant")
            parsed_shares[parsed_user_id] = parse_splitwise_amount(share, "owed_shares values")
    except (TypeError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith("owed_shares"):
            raise
        raise ValueError("owed_shares keys must be Splitwise user IDs") from exc

    if set(parsed_shares) != set(participant_ids):
        raise ValueError("owed_shares participants must match the current user and selected friends")
    if sum(parsed_shares.values(), Decimal("0.00")) != amount:
        raise ValueError("owed_shares must add up to the expense amount")
    return parsed_shares


def build_equal_owed_shares(amount: Decimal, participant_ids: List[int]) -> Dict[int, Decimal]:
    share = Decimal(format_money(amount / Decimal(len(participant_ids))))
    remainder = amount - (share * (len(participant_ids) - 1))
    return {
        user_id: remainder if index == len(participant_ids) - 1 else share for index, user_id in enumerate(participant_ids)
    }


def build_splitwise_expense(
    amount: Decimal,
    description: str,
    current_user_id: int,
    owed_shares: Dict[int, Decimal],
    currency_code: str,
    date: str | None,
) -> Expense:
    expense = Expense()
    expense.setDescription(description)
    expense.setCost(format_money(amount))
    expense.setCurrencyCode(currency_code)
    expense.setUsers(build_splitwise_users(amount, current_user_id, owed_shares))
    if date:
        expense.setDate(date)
    return expense


def build_splitwise_users(amount: Decimal, current_user_id: int, owed_shares: Dict[int, Decimal]) -> List[ExpenseUser]:
    users: List[ExpenseUser] = []
    for user_id, owed_share in owed_shares.items():
        user = ExpenseUser()
        user.setId(user_id)
        user.setPaidShare(format_money(amount) if user_id == current_user_id else "0.00")
        user.setOwedShare(format_money(owed_share))
        users.append(user)
    return users


def refresh_splitwise() -> None:
    logger.info("Refreshing Splitwise Data")

    # Page through all expenses; a single call is capped at LIMIT results
    expenses: List[Any] = []
    offset = 0
    while True:
        page: List[Any] = splitwise_client.getExpenses(limit=LIMIT, offset=offset, dated_after=MOVING_DATE)
        expenses.extend(page)
        if len(page) < LIMIT:
            break
        offset += LIMIT

    all_expenses: List[Any] = [expense for expense in expenses if expense.deleted_at is None]
    deleted_source_ids: List[str] = [str(expense.id) for expense in expenses if expense.deleted_at is not None]

    if all_expenses or deleted_source_ids:
        with SessionLocal.begin() as db:
            bulk_upsert_transactions(db, all_expenses, source="splitwise_api")
            # Remove expenses deleted in Splitwise (unless already reviewed into an event)
            delete_transactions_for_removed_sources(db, "splitwise_api", deleted_source_ids)
        logger.info(f"Refreshed {len(all_expenses)} Splitwise expenses ({len(deleted_source_ids)} deleted upstream)")
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
