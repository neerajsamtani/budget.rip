import datetime
import logging
from typing import Any, Dict, List, Optional, TypedDict

import stripe
from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required

from constants import STRIPE_API_KEY, STRIPE_CUSTOMER_ID
from dao import (
    bank_accounts_collection,
    bulk_upsert,
    get_all_data,
    line_items_collection,
    stripe_raw_account_data_collection,
    stripe_raw_transaction_data_collection,
    upsert,
)
from helpers import cents_to_dollars, flip_amount
from resources.line_item import LineItem
from utils.dual_write import dual_write_operation
from utils.pg_bulk_ops import (
    bulk_upsert_bank_accounts,
    bulk_upsert_line_items,
    bulk_upsert_transactions,
)

stripe_blueprint = Blueprint("stripe", __name__)

if STRIPE_API_KEY is None:
    raise Exception("Stripe API Key is not set")
if STRIPE_CUSTOMER_ID is None:
    raise Exception("Stripe Customer ID is not set")

stripe.api_version = "2022-08-01; financial_connections_transactions_beta=v1; financial_connections_relink_api_beta=v1"


class BankAccountData(TypedDict, total=False):
    """Type-safe representation of bank account data."""

    id: str
    _id: str  # MongoDB ID
    institution_name: str
    display_name: str
    last4: str
    status: str
    authorization: str
    can_relink: bool


def to_bank_account_data(account: stripe.financial_connections.Account, can_relink: Optional[bool] = None) -> BankAccountData:
    """
    Convert Stripe Account object to typed BankAccountData.

    Args:
        account: Stripe Account object
        can_relink: Optional override for can_relink status. If None, will be computed.

    Returns:
        Type-safe BankAccountData dict
    """
    if can_relink is None:
        can_relink = check_can_relink(account)

    return BankAccountData(
        id=account["id"],
        _id=account.get("_id", account["id"]),  # Use id as fallback
        institution_name=account.get("institution_name", ""),
        display_name=account.get("display_name", ""),
        last4=account.get("last4", ""),
        status=account.get("status", "active"),
        authorization=account.get("authorization", ""),
        can_relink=can_relink,
    )


def check_can_relink(account: stripe.financial_connections.Account) -> bool:
    """
    Check if an inactive account can be relinked based on authorization status.

    Returns True if:
    - Account is active, OR
    - Account is inactive AND authorization.status_details.inactive.action == 'relink_required'

    Returns False if:
    - Account is inactive AND authorization.status_details.inactive.action == 'none'
    - Account is inactive but authorization is active (e.g., account closed at institution)
    """
    # If account is active, it can always be "relinked" (refreshed)
    if account.get("status") == "active":
        return True

    # If account is inactive, check authorization status
    if account.get("status") == "inactive":
        try:
            auth_id = account.get("authorization")
            if not auth_id:
                return False

            # Use Stripe SDK to retrieve authorization
            authorization = stripe.financial_connections.Authorization.retrieve(auth_id)

            # If authorization is active but account is inactive, account cannot be relinked
            # (e.g., account closed at institution)
            if authorization.get("status") == "active":
                return False

            # If authorization is inactive, check if relink is required
            if authorization.get("status") == "inactive":
                status_details = authorization.get("status_details", {})
                inactive_details = status_details.get("inactive", {})
                action = inactive_details.get("action")
                return action == "relink_required"

            return False
        except Exception as e:
            logging.error(f"Error checking relink status for account {account.get('id')}: {e}")
            # Default to True to be safe - let user try to relink
            return True

    # Default case
    return True


@stripe_blueprint.route("/api/refresh/stripe")
@jwt_required()
def refresh_stripe_api() -> tuple[Response, int]:
    refresh_stripe()
    return jsonify("Refreshed Stripe Connection"), 200


@stripe_blueprint.route("/api/create-fc-session", methods=["POST"])
@jwt_required()
def create_fc_session_api(
    relink_auth: Optional[str] = None,
) -> tuple[Response, int]:
    try:
        # Get or create customer
        try:
            customer: stripe.Customer = stripe.Customer.retrieve(STRIPE_CUSTOMER_ID)
        except stripe.InvalidRequestError:
            logging.info("Creating a new customer...")
            customer: stripe.Customer = stripe.Customer.create(email="neeraj@gmail.com", name="Neeraj")

        # Create Financial Connections session using Stripe SDK
        session_params: Dict[str, Any] = {
            "account_holder": {"type": "customer", "customer": customer["id"]},
            "permissions": ["transactions", "balances"],
        }

        # Add relink_options if provided
        if relink_auth:
            session_params["relink_options"] = {"authorization": relink_auth}

        session = stripe.financial_connections.Session.create(**session_params)

        return jsonify({"clientSecret": session["client_secret"]}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@stripe_blueprint.route("/api/create_accounts", methods=["POST"])
@jwt_required()
def create_accounts_api() -> tuple[Response, int]:
    new_accounts: List[Dict[str, Any]] = request.get_json()
    if len(new_accounts) == 0:
        return jsonify("Failed to Create Accounts: No Accounts Submitted"), 400

    dual_write_operation(
        mongo_write_func=lambda: bulk_upsert(bank_accounts_collection, new_accounts),
        pg_write_func=lambda db: bulk_upsert_bank_accounts(db, new_accounts),
        operation_name="create_bank_accounts",
    )

    return jsonify({"data": new_accounts}), 201


@stripe_blueprint.route("/api/get_accounts/<session_id>")
@jwt_required()
def get_accounts_api(session_id: str) -> tuple[Response, int]:
    try:
        session: stripe.financial_connections.Session = stripe.financial_connections.Session.retrieve(session_id)
        accounts: List[Dict[str, Any]] = session["accounts"]

        # Bulk upsert all accounts at once
        bulk_upsert(stripe_raw_account_data_collection, accounts)

        return jsonify({"accounts": accounts}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@stripe_blueprint.route("/api/accounts_and_balances")
@jwt_required()
def get_accounts_and_balances_api() -> tuple[Response, int]:
    """
    Get all accounts with their current balances.

    Note: This has an N+1 query problem - we fetch balance for each account separately.
    Stripe doesn't provide a batch endpoint for balances, so we'd need to either:
    1. Add caching
    2. Make calls concurrently (asyncio/threading)
    3. Store balances in DB and refresh periodically

    For now, using SDK and adding error handling per account.
    """
    accounts: List[Dict[str, Any]] = get_all_data(bank_accounts_collection)
    accounts_and_balances: Dict[str, Dict[str, Any]] = {}

    for account in accounts:
        account_id: str = account["id"]
        account_name: str = f"{account['institution_name']} {account['display_name']} {account['last4']}"

        try:
            # Use Stripe SDK to list inferred balances for the account
            balances = stripe.financial_connections.Account.list_inferred_balances(account_id, limit=1)

            balance_data = balances["data"][0] if balances.get("data") else None
            balance_usd = balance_data["current"]["usd"] / 100 if balance_data else 0
            as_of = balance_data["as_of"] if balance_data else None

            accounts_and_balances[account_id] = {
                "id": account_id,
                "name": account_name,
                "balance": balance_usd,
                "as_of": as_of,
                "status": account["status"],
                "can_relink": account.get("can_relink", True),
            }
        except Exception as e:
            logging.error(f"Error fetching balance for account {account_id}: {e}")
            # Return account info even if balance fetch fails
            accounts_and_balances[account_id] = {
                "id": account_id,
                "name": account_name,
                "balance": 0,
                "as_of": None,
                "status": account["status"],
                "can_relink": account.get("can_relink", True),
            }

    return jsonify(accounts_and_balances), 200


@stripe_blueprint.route("/api/subscribe_to_account", methods=["POST"])
@jwt_required()
def subscribe_to_account_api() -> tuple[Response, int]:
    try:
        account_id: str = request.json.get("account_id")
        if not account_id:
            return jsonify({"error": "account_id is required"}), 400

        # Subscribe to account features using Stripe SDK's generic API request
        response = stripe.financial_connections.Account.subscribe(account_id, features=["transactions", "inferred_balances"])

        refresh_status: str = response.get("transaction_refresh", {}).get("status", "unknown")
        return jsonify(str(refresh_status)), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@stripe_blueprint.route("/api/refresh_account/<account_id>")
def refresh_account_api(account_id: str) -> tuple[Response, int]:
    try:
        logging.info(f"Refreshing {account_id}")
        account: stripe.financial_connections.Account = stripe.financial_connections.Account.retrieve(account_id)

        # Convert to typed account data with can_relink status
        account_data = to_bank_account_data(account)

        dual_write_operation(
            mongo_write_func=lambda: upsert(bank_accounts_collection, account_data),
            pg_write_func=lambda db: bulk_upsert_bank_accounts(db, [account_data]),
            operation_name="refresh_bank_account",
        )
        return jsonify({"data": "success"}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@stripe_blueprint.route("/api/relink_account/<account_id>", methods=["POST"])
@jwt_required()
def relink_account_api(account_id: str) -> tuple[Response, int]:
    try:
        logging.info(f"Relinking {account_id}")

        account: stripe.financial_connections.Account = stripe.financial_connections.Account.retrieve(account_id)

        # Check if account can be relinked using our helper
        if not check_can_relink(account):
            return jsonify({"relink_required": False}), 200

        # Create a new session for relinking
        create_fc_session_response = create_fc_session_api(account["authorization"])
        return jsonify(create_fc_session_response[0].json), 200

    except Exception as e:
        return jsonify(error=str(e)), 500


@stripe_blueprint.route("/api/refresh_transactions/<account_id>")
def refresh_transactions_api(account_id: str) -> tuple[Response, int]:
    logging.info(f"Getting Transactions for {account_id}")
    # TODO: This gets all transactions ever. We should only get those that we don't have
    try:
        has_more: bool = True
        starting_after = ""

        # Collect all transactions for bulk upsert
        all_transactions: List[Dict[str, Any]] = []
        stripe.api_key = STRIPE_API_KEY
        stripe.api_version = "2022-08-01; financial_connections_transactions_beta=v1"

        while has_more:
            # Print human readable time
            logging.info(
                "Last request at: ",
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            transactions_list_params = {
                "account": account_id,
                "limit": 100,
            }
            if starting_after:
                transactions_list_params["starting_after"] = starting_after

            transactions_list_object = stripe.financial_connections.Transaction.list(**transactions_list_params)

            transactions = transactions_list_object.data

            for transaction in transactions:
                if transaction.status == "posted":
                    all_transactions.append(transaction)
                elif transaction.status == "pending":
                    logging.info(
                        f"Pending Transaction: {transaction.description} | "
                        + f"{cents_to_dollars(flip_amount(transaction.amount))}"
                    )

            has_more = transactions_list_object.has_more
            starting_after = transactions[-1].id if transactions else ""

        # Bulk upsert all collected transactions at once
        if all_transactions:
            dual_write_operation(
                mongo_write_func=lambda: bulk_upsert(stripe_raw_transaction_data_collection, all_transactions),
                pg_write_func=lambda db: bulk_upsert_transactions(db, all_transactions, source="stripe"),
                operation_name="stripe_refresh_transactions",
            )

        # If we want to enable only refreshing a single account, we need to uncomment this
        # stripe_to_line_items()
        return jsonify("Refreshed Stripe Connection for Given Account"), 200

    except Exception as e:
        return jsonify(error=str(e)), 500


def refresh_stripe() -> None:
    logging.info("Refreshing Stripe Data")
    bank_accounts: List[Dict[str, Any]] = get_all_data(bank_accounts_collection)
    for account in bank_accounts:
        refresh_account_api(account["id"])
        refresh_transactions_api(account["id"])
    stripe_to_line_items()


def stripe_to_line_items() -> None:
    """
    Convert Stripe transactions to line items with optimized database operations.

    Optimizations:
    1. Pre-fetch all accounts and create a lookup dictionary to avoid repeated database calls
    2. Use bulk upsert operations instead of individual upserts
    3. Process transactions in batches to handle large datasets efficiently
    """
    # Pre-fetch all accounts and create a lookup dictionary
    all_accounts: List[Dict[str, Any]] = get_all_data(bank_accounts_collection)
    account_lookup: Dict[str, Dict[str, Any]] = {account["_id"]: account for account in all_accounts}

    # Get all stripe transactions
    stripe_raw_data: List[Dict[str, Any]] = get_all_data(stripe_raw_transaction_data_collection)

    # Process transactions in batches for better memory management
    batch_size: int = 1000
    line_items_batch: List[LineItem] = []

    for transaction in stripe_raw_data:
        # Use memoized account lookup instead of database call
        transaction_account: Optional[Dict[str, Any]] = account_lookup.get(transaction["account"])

        if transaction_account:
            payment_method: str = transaction_account["display_name"]
        else:
            # Fallback to default if account not found
            payment_method = "Stripe"

        line_item = LineItem(
            f"line_item_{transaction['_id']}",
            transaction["transacted_at"],
            transaction["description"],
            payment_method,
            transaction["description"],
            flip_amount(transaction["amount"]) / 100,
        )

        line_items_batch.append(line_item)

        # Bulk upsert when batch is full
        if len(line_items_batch) >= batch_size:
            dual_write_operation(
                mongo_write_func=lambda: bulk_upsert(line_items_collection, line_items_batch),
                pg_write_func=lambda db: bulk_upsert_line_items(db, line_items_batch, source="stripe"),
                operation_name="stripe_create_line_items",
            )
            line_items_batch = []

    # Upsert remaining items in the final batch
    if line_items_batch:
        dual_write_operation(
            mongo_write_func=lambda: bulk_upsert(line_items_collection, line_items_batch),
            pg_write_func=lambda db: bulk_upsert_line_items(db, line_items_batch, source="stripe"),
            operation_name="stripe_create_line_items",
        )
