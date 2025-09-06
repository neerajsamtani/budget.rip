import datetime
import json
import logging
from typing import Any, Dict, List, Optional

import requests
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
from models import LineItem

stripe_blueprint = Blueprint("stripe", __name__)

if STRIPE_API_KEY is None:
    raise Exception("Stripe API Key is not set")
if STRIPE_CUSTOMER_ID is None:
    raise Exception("Stripe Customer ID is not set")

stripe.api_version = "2022-08-01; financial_connections_transactions_beta=v1; financial_connections_relink_api_beta=v1"


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
        # TODO: Is there a better pattern than nested trys?
        try:
            customer: stripe.Customer = stripe.Customer.retrieve(STRIPE_CUSTOMER_ID)
        except stripe.InvalidRequestError:
            logging.info("Creating a new customer...")
            customer: stripe.Customer = stripe.Customer.create(
                email="neeraj@gmail.com", name="Neeraj"
            )

        # API endpoint
        url: str = "https://api.stripe.com/v1/financial_connections/sessions"

        headers: Dict[str, str] = {
            "Stripe-Version": "2022-08-01; financial_connections_transactions_beta=v1; financial_connections_relink_api_beta=v1",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Payload
        data: Dict[str, Any] = {
            "account_holder[type]": "customer",
            "account_holder[customer]": customer["id"],
            "permissions[]": ["transactions", "balances"],
        }

        # Add relink_options[authorization] if provided
        if relink_auth:
            data["relink_options[authorization]"] = relink_auth

        # Make the request
        session: requests.Response = requests.post(
            url, headers=headers, data=data, auth=(STRIPE_API_KEY, "")
        )

        return jsonify({"clientSecret": session.json()["client_secret"]}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@stripe_blueprint.route("/api/create_accounts", methods=["POST"])
@jwt_required()
def create_accounts_api() -> tuple[Response, int]:
    new_accounts: List[Dict[str, Any]] = request.get_json()
    if len(new_accounts) == 0:
        return jsonify("Failed to Create Accounts: No Accounts Submitted"), 400
    bulk_upsert(bank_accounts_collection, new_accounts)
    return jsonify({"data": new_accounts}), 201


@stripe_blueprint.route("/api/get_accounts/<session_id>")
@jwt_required()
def get_accounts_api(session_id: str) -> tuple[Response, int]:
    try:
        session = stripe.financial_connections.Session.retrieve(session_id)
        accounts = session.accounts.data
        bulk_upsert(stripe_raw_account_data_collection, accounts)
        return jsonify({"accounts": accounts}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@stripe_blueprint.route("/api/accounts_and_balances")
@jwt_required()
def get_accounts_and_balances_api() -> tuple[Response, int]:
    accounts: List[Dict[str, Any]] = get_all_data(bank_accounts_collection)
    accounts_and_balances: Dict[str, Dict[str, Any]] = {}
    for account in accounts:
        account_id: str = account["id"]
        headers: Dict[str, str] = {
            "Stripe-Version": "2022-08-01;",
        }
        data: Dict[str, int] = {
            "limit": 1,
        }
        response: requests.Response = requests.get(
            f"https://api.stripe.com/v1/financial_connections/accounts/{account_id}/inferred_balances",
            headers=headers,
            data=data,
            auth=(STRIPE_API_KEY, ""),
        )
        account_name: str = (
            f'{account["institution_name"]} {account["display_name"]} {account["last4"]}'
        )
        response_data: List[Dict[str, Any]] = response.json()["data"]
        accounts_and_balances[account_id] = {
            "id": account_id,
            "name": account_name,
            "balance": (
                response_data[0]["current"]["usd"] / 100
                if len(response_data) > 0
                else 0
            ),
            "as_of": response_data[0]["as_of"] if len(response_data) > 0 else None,
            "status": account["status"],
        }

    return jsonify(accounts_and_balances), 200


@stripe_blueprint.route("/api/subscribe_to_account/<account_id>")
@jwt_required()
def subscribe_to_account_api(account_id: str) -> tuple[Response, int]:
    try:
        # Use requests since we cannot subscribe to an account with the Stripe Python client
        headers: Dict[str, str] = {
            "Stripe-Version": "2022-08-01; financial_connections_transactions_beta=v1",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data: Dict[str, List[str]] = {
            "features[]": ["transactions", "inferred_balances"],
        }
        response: requests.Response = requests.post(
            f"https://api.stripe.com/v1/financial_connections/accounts/{account_id}/subscribe",
            headers=headers,
            data=data,
            auth=(STRIPE_API_KEY, ""),
        )
        refresh_status: str = json.loads(response.text)["transaction_refresh"]["status"]
        return jsonify(str(refresh_status)), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@stripe_blueprint.route("/api/refresh_account/<account_id>")
def refresh_account_api(account_id: str) -> tuple[Response, int]:
    try:
        logging.info(f"Refreshing {account_id}")
        account = stripe.financial_connections.Account.retrieve(account_id)
        upsert(bank_accounts_collection, account)
        return jsonify({"data": "success"}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@stripe_blueprint.route("/api/relink_account/<account_id>")
@jwt_required()
def relink_account_api(account_id: str) -> tuple[Response, int]:
    try:
        logging.info(f"Relinking {account_id}")

        account = stripe.financial_connections.Account.retrieve(account_id)
        headers: Dict[str, str] = {
            "Stripe-Version": "2022-08-01; financial_connections_transactions_beta=v1; financial_connections_relink_api_beta=v1",
        }
        response: requests.Response = requests.get(
            f"https://api.stripe.com/v1/financial_connections/authorizations/{account['authorization']}",
            headers=headers,
            auth=(STRIPE_API_KEY, ""),
        )
        if response.json()["status_details"]["inactive"]["action"] != "relink_required":
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

            transactions_list_object = stripe.financial_connections.Transaction.list(
                **transactions_list_params
            )

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
            bulk_upsert(stripe_raw_transaction_data_collection, all_transactions)

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
    account_lookup: Dict[str, Dict[str, Any]] = {
        account["_id"]: account for account in all_accounts
    }

    # Get all stripe transactions
    stripe_raw_data: List[Dict[str, Any]] = get_all_data(
        stripe_raw_transaction_data_collection
    )

    # Process transactions in batches for better memory management
    batch_size: int = 1000
    line_items_batch: List[LineItem] = []

    for transaction in stripe_raw_data:
        # Use memoized account lookup instead of database call
        transaction_account: Optional[Dict[str, Any]] = account_lookup.get(
            transaction["account"]
        )

        if transaction_account:
            payment_method: str = transaction_account["display_name"]
        else:
            # Fallback to default if account not found
            payment_method = "Stripe"

        line_item = LineItem(
            id=f'line_item_{transaction["_id"]}',
            date=transaction["transacted_at"],
            responsible_party=transaction["description"],
            payment_method=payment_method,
            description=transaction["description"],
            amount=flip_amount(transaction["amount"]) / 100,
        )

        line_items_batch.append(line_item)

        # Bulk upsert when batch is full
        if len(line_items_batch) >= batch_size:
            bulk_upsert(line_items_collection, line_items_batch)
            line_items_batch = []

    # Upsert remaining items in the final batch
    if line_items_batch:
        bulk_upsert(line_items_collection, line_items_batch)
