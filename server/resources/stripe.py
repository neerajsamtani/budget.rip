import logging
from typing import Any, Dict, List, Optional

import requests  # Still needed for Authorization endpoint (not yet in SDK)
import stripe
from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required

from constants import BATCH_SIZE, STRIPE_API_KEY, STRIPE_CUSTOMER_EMAIL, STRIPE_CUSTOMER_ID, STRIPE_CUSTOMER_NAME
from dao import (
    bank_accounts_collection,
    get_all_data,
    stripe_raw_transaction_data_collection,
)
from helpers import cents_to_dollars, flip_amount
from resources.line_item import LineItem
from type_defs import StripeAuthorizationDict
from utils.pg_bulk_ops import (
    upsert_bank_accounts,
    upsert_line_items,
    upsert_transactions,
)
from utils.validation import require_field

logger = logging.getLogger(__name__)

stripe_blueprint = Blueprint("stripe", __name__)

if STRIPE_API_KEY is None:
    raise Exception("Stripe API Key is not set")
if STRIPE_CUSTOMER_ID is None:
    raise Exception("Stripe Customer ID is not set")

stripe.api_version = "2022-08-01; financial_connections_transactions_beta=v1; financial_connections_relink_api_beta=v1"

# Initialize StripeClient for service-based API access
stripe_client = stripe.StripeClient(api_key=STRIPE_API_KEY)


def check_can_relink(account: stripe.financial_connections.Account) -> bool:
    """Check if inactive account can be relinked. Active accounts return False (don't need relink).

    Args:
        account: Stripe financial connections account

    Returns:
        True if account is inactive and can be relinked, False otherwise
    """
    # Active accounts don't need relinking
    status = account.get("status")
    if status == "active":
        return False

    if status == "inactive":
        try:
            auth_id = account.get("authorization")
            if not auth_id:
                logger.warning(f"Inactive account {account.get('id')} has no authorization ID")
                return False

            response = requests.get(
                f"https://api.stripe.com/v1/financial_connections/authorizations/{auth_id}",
                headers={"Stripe-Version": "2022-08-01; financial_connections_relink_api_beta=v1"},
                auth=(STRIPE_API_KEY, ""),
            )
            authorization: StripeAuthorizationDict = response.json()

            # Account closed at institution - can't relink even if auth is still active
            auth_status = authorization.get("status")
            if auth_status == "active":
                return False

            if auth_status == "inactive":
                # Use nested get() with explicit None checks for optional Stripe API fields
                status_details = authorization.get("status_details")
                if not status_details:
                    return False

                inactive_details = status_details.get("inactive")
                if not inactive_details:
                    return False

                return inactive_details.get("action") == "relink_required"

            return False
        except Exception as e:
            logger.error(f"Error checking relink status for account {account.get('id')}: {e}")
            return False  # Default to False on error - safer than allowing broken relinks

    return False


def refresh_account_balances(account_ids: Optional[List[str]] = None) -> int:
    """
    Fetch and store latest balance for Stripe accounts (best-effort operation).

    Solves N+1 problem: Previously fetched balances via N individual Stripe API
    calls during page load. Now pre-fetches and stores on account records.

    Best-effort: Balance refresh failures are logged but don't break parent operations
    (account/transaction refresh). Balances are supplementary data.

    Args:
        account_ids: Optional list of specific account IDs to refresh. If None, refreshes all accounts.

    Returns:
        Count of accounts updated with balance info
    """
    from datetime import datetime, timezone

    if account_ids:
        all_accounts = get_all_data(bank_accounts_collection)
        accounts = [acc for acc in all_accounts if acc["id"] in account_ids]
    else:
        accounts = get_all_data(bank_accounts_collection)

    updated_count = 0

    for account in accounts:
        account_id = account["id"]

        try:
            logger.info(f"Fetching latest balance for account {account_id}")

            # Fetch latest balance only (limit=1)
            balances = stripe_client.v1.financial_connections.accounts.inferred_balances.list(
                account=account_id,
                params={"limit": 1},
            )

            if balances.data:
                balance_data = balances.data[0]
                # Stripe inferred balances support multiple currencies
                currency = next(iter(balance_data.current.keys()))
                balance_cents = balance_data.current[currency]

                account["currency"] = currency
                account["latest_balance"] = balance_cents / 100  # Convert from cents
                account["balance_as_of"] = datetime.fromtimestamp(balance_data.as_of, tz=timezone.utc)

                upsert_bank_accounts([account])

                updated_count += 1
                logger.info(f"Updated balance for account {account_id}: {balance_cents / 100} {currency}")

        except Exception as e:
            logger.error(f"Error fetching balance for account {account_id}: {e}")
            # Continue with other accounts even if one fails

    return updated_count


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
        try:
            customer: stripe.Customer = stripe.Customer.retrieve(STRIPE_CUSTOMER_ID)
        except stripe.InvalidRequestError:
            logger.info("Creating a new customer...")
            customer: stripe.Customer = stripe.Customer.create(email=STRIPE_CUSTOMER_EMAIL, name=STRIPE_CUSTOMER_NAME)

        session_params: Dict[str, Any] = {
            "account_holder": {"type": "customer", "customer": customer["id"]},
            "permissions": ["transactions", "balances"],
        }

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

    upsert_bank_accounts(new_accounts)

    return jsonify({"data": new_accounts}), 201


@stripe_blueprint.route("/api/get_accounts/<session_id>")
@jwt_required()
def get_accounts_api(session_id: str) -> tuple[Response, int]:
    try:
        session: stripe.financial_connections.Session = stripe.financial_connections.Session.retrieve(session_id)
        accounts: List[Dict[str, Any]] = session["accounts"]

        upsert_bank_accounts(accounts)

        return jsonify({"accounts": accounts}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@stripe_blueprint.route("/api/accounts_and_balances")
@jwt_required()
def get_accounts_and_balances_api() -> tuple[Response, int]:
    """
    Get bank accounts with their latest balances.

    Balances are pre-fetched and stored on account records via refresh_account_balances()
    to avoid N+1 query problem (previously made one Stripe API call per account).
    """
    accounts: List[Dict[str, Any]] = get_all_data(bank_accounts_collection)
    accounts_and_balances: Dict[str, Dict[str, Any]] = {}

    for account in accounts:
        account_id: str = account["id"]
        account_name: str = f"{account['institution_name']} {account['display_name']} {account['last4']}"

        if "can_relink" not in account:
            account["can_relink"] = check_can_relink(account)

        balance = account.get("latest_balance", 0)
        as_of_dt = account.get("balance_as_of")
        as_of = int(as_of_dt.timestamp()) if as_of_dt else None
        currency = account.get("currency", "usd")

        accounts_and_balances[account_id] = {
            "id": account_id,
            "name": account_name,
            "balance": balance,
            "currency": currency,
            "as_of": as_of,
            "status": account["status"],
            "can_relink": account["can_relink"],
        }

    return jsonify(accounts_and_balances), 200


@stripe_blueprint.route("/api/subscribe_to_account", methods=["POST"])
@jwt_required()
def subscribe_to_account_api() -> tuple[Response, int]:
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "Request body is required"}), 400

        account_id = require_field(request_data, "account_id", "subscribe request")

        response = stripe.financial_connections.Account.subscribe(account_id, features=["transactions", "inferred_balances"])
        refresh_status: str = response.get("transaction_refresh", {}).get("status", "unknown")
        return jsonify(str(refresh_status)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify(error=str(e)), 500


@stripe_blueprint.route("/api/refresh_account/<account_id>")
def refresh_account_api(account_id: str) -> tuple[Response, int]:
    try:
        logger.info(f"Refreshing {account_id}")
        account: stripe.financial_connections.Account = stripe.financial_connections.Account.retrieve(account_id)
        account["can_relink"] = check_can_relink(account)

        upsert_bank_accounts([account])

        return jsonify({"data": "success"}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@stripe_blueprint.route("/api/relink_account/<account_id>", methods=["POST"])
@jwt_required()
def relink_account_api(account_id: str) -> tuple[Response, int]:
    try:
        logger.info(f"Relinking {account_id}")
        account: stripe.financial_connections.Account = stripe.financial_connections.Account.retrieve(account_id)

        if not check_can_relink(account):
            return jsonify({"relink_required": False}), 200

        create_fc_session_response = create_fc_session_api(account["authorization"])
        return jsonify(create_fc_session_response[0].json), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@stripe_blueprint.route("/api/refresh_transactions/<account_id>")
def refresh_transactions_api(account_id: str) -> tuple[Response, int]:
    logger.info(f"Getting Transactions for {account_id}")
    # TODO: This gets all transactions ever. We should only get those that we don't have
    try:
        has_more: bool = True
        starting_after = ""
        all_transactions: List[Dict[str, Any]] = []
        stripe.api_key = STRIPE_API_KEY
        stripe.api_version = "2022-08-01; financial_connections_transactions_beta=v1"

        while has_more:
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
                    logger.info(
                        f"Pending Transaction: {transaction.description} | "
                        + f"{cents_to_dollars(flip_amount(transaction.amount))}"
                    )

            has_more = transactions_list_object.has_more
            starting_after = transactions[-1].id if transactions else ""

        if all_transactions:
            upsert_transactions(all_transactions, source="stripe")

        # Best-effort: fetch latest balance for this account (won't fail transaction refresh)
        refresh_account_balances(account_ids=[account_id])

        return jsonify("Refreshed Stripe Connection for Given Account"), 200

    except Exception as e:
        return jsonify(error=str(e)), 500


def refresh_stripe() -> None:
    logger.info("Refreshing Stripe Data")
    bank_accounts: List[Dict[str, Any]] = get_all_data(bank_accounts_collection)
    for account in bank_accounts:
        refresh_account_api(account["id"])
        refresh_transactions_api(account["id"])
    stripe_to_line_items()
    # Best-effort: refresh balances for all accounts after transactions updated
    refresh_account_balances()


def stripe_to_line_items() -> None:
    """
    Convert Stripe transactions to line items with optimized database operations.

    Optimizations:
    1. Pre-fetch all accounts and create a lookup dictionary to avoid repeated database calls
    2. Use bulk upsert operations instead of individual upserts
    3. Process transactions in batches to handle large datasets efficiently
    """
    all_bank_accounts: List[Dict[str, Any]] = get_all_data(bank_accounts_collection)
    bank_account_lookup: Dict[str, Dict[str, Any]] = {account["id"]: account for account in all_bank_accounts}

    stripe_raw_data: List[Dict[str, Any]] = get_all_data(stripe_raw_transaction_data_collection)

    line_items_batch: List[LineItem] = []

    for stripe_transaction in stripe_raw_data:
        # Use memoized account lookup instead of database call
        stripe_account: Optional[Dict[str, Any]] = bank_account_lookup.get(stripe_transaction["account"])

        if stripe_account:
            payment_method: str = stripe_account["display_name"]
        else:
            payment_method = "Stripe"

        line_item = LineItem(
            stripe_transaction["transacted_at"],
            stripe_transaction["description"],
            payment_method,
            stripe_transaction["description"],
            flip_amount(stripe_transaction["amount"]) / 100,
            source_id=str(stripe_transaction["source_id"]),
        )

        line_items_batch.append(line_item)

        if len(line_items_batch) >= BATCH_SIZE:
            upsert_line_items(line_items_batch, source="stripe")
            line_items_batch = []

    if line_items_batch:
        upsert_line_items(line_items_batch, source="stripe")
