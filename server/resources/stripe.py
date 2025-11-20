import datetime
import logging
from typing import Any, Dict, List, Optional

import requests  # Still needed for Authorization endpoint (not yet in SDK)
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

# Initialize StripeClient for service-based API access
stripe_client = stripe.StripeClient(api_key=STRIPE_API_KEY)


def check_can_relink(account: stripe.financial_connections.Account) -> bool:
    """Check if inactive account can be relinked. Active accounts return False (don't need relink)."""
    if account.get("status") == "active":
        return False  # Active accounts don't need relinking

    if account.get("status") == "inactive":
        try:
            auth_id = account.get("authorization")
            if not auth_id:
                return False

            response = requests.get(
                f"https://api.stripe.com/v1/financial_connections/authorizations/{auth_id}",
                headers={"Stripe-Version": "2022-08-01; financial_connections_relink_api_beta=v1"},
                auth=(STRIPE_API_KEY, ""),
            )
            authorization = response.json()

            # Account closed at institution - can't relink even if auth is still active
            if authorization.get("status") == "active":
                return False

            if authorization.get("status") == "inactive":
                status_details = authorization.get("status_details", {})
                inactive_details = status_details.get("inactive", {})
                return inactive_details.get("action") == "relink_required"

            return False
        except Exception as e:
            logging.error(f"Error checking relink status for account {account.get('id')}: {e}")
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
    from dao import upsert_with_id

    # Get accounts to refresh
    if account_ids:
        all_accounts = get_all_data(bank_accounts_collection)
        accounts = [acc for acc in all_accounts if acc["id"] in account_ids]
    else:
        accounts = get_all_data(bank_accounts_collection)

    updated_count = 0

    for account in accounts:
        account_id = account["id"]

        try:
            logging.info(f"Fetching latest balance for account {account_id}")

            # Fetch latest balance only (limit=1)
            balances = stripe_client.v1.financial_connections.accounts.inferred_balances.list(
                account=account_id,
                params={"limit": 1},
            )

            if balances.data:
                balance_data = balances.data[0]
                # Get the currency and balance (Stripe inferred balances support multiple currencies)
                # Use the first currency available
                currency = next(iter(balance_data.current.keys()))
                balance_cents = balance_data.current[currency]

                # Update account with latest balance
                account["currency"] = currency
                account["latest_balance"] = balance_cents / 100  # Convert from cents
                account["balance_as_of"] = datetime.fromtimestamp(balance_data.as_of, tz=timezone.utc)

                # Dual-write updated account
                dual_write_operation(
                    mongo_write_func=lambda: upsert_with_id(bank_accounts_collection, account, account_id),
                    pg_write_func=lambda db: bulk_upsert_bank_accounts(db, [account]),
                    operation_name=f"refresh_balance_{account_id}",
                )
                updated_count += 1
                logging.info(f"Updated balance for account {account_id}: {balance_cents / 100} {currency}")

        except Exception as e:
            logging.error(f"Error fetching balance for account {account_id}: {e}")
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
            logging.info("Creating a new customer...")
            customer: stripe.Customer = stripe.Customer.create(email="neeraj@gmail.com", name="Neeraj")

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
    Get bank accounts with their latest balances.

    Balances are pre-fetched and stored on account records via refresh_account_balances()
    to avoid N+1 query problem (previously made one Stripe API call per account).
    """
    accounts: List[Dict[str, Any]] = get_all_data(bank_accounts_collection)
    accounts_and_balances: Dict[str, Dict[str, Any]] = {}

    for account in accounts:
        account_id: str = account["id"]
        account_name: str = f"{account['institution_name']} {account['display_name']} {account['last4']}"

        # Calculate can_relink if not already in DB
        if "can_relink" not in account:
            account["can_relink"] = check_can_relink(account)

        # Get balance from account record
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
        account_id: str = request.json.get("account_id")
        if not account_id:
            return jsonify({"error": "account_id is required"}), 400

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
        account["can_relink"] = check_can_relink(account)

        dual_write_operation(
            mongo_write_func=lambda: upsert(bank_accounts_collection, account),
            pg_write_func=lambda db: bulk_upsert_bank_accounts(db, [account]),
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

        if not check_can_relink(account):
            return jsonify({"relink_required": False}), 200

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

        # Best-effort: fetch latest balance for this account (won't fail transaction refresh)
        refresh_account_balances(account_ids=[account_id])

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
