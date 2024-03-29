import json

import requests
from constants import STRIPE_API_KEY, STRIPE_CUSTOMER_ID
from dao import (
    bank_accounts_collection,
    get_all_data,
    get_item_by_id,
    line_items_collection,
    stripe_raw_account_data_collection,
    stripe_raw_transaction_data_collection,
    upsert,
)
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from helpers import flip_amount

import stripe
from resources.line_item import LineItem
from helpers import cents_to_dollars

stripe_blueprint = Blueprint("stripe", __name__)


@stripe_blueprint.route("/api/refresh/stripe")
@jwt_required()
def refresh_stripe_api():
    refresh_stripe()
    return jsonify("Refreshed Stripe Connection")


@stripe_blueprint.route("/api/create-fc-session", methods=["POST"])
@jwt_required()
def create_fc_session_api():
    try:
        # TODO: Is there a better pattern than nested trys?
        try:
            customer = stripe.Customer.retrieve(STRIPE_CUSTOMER_ID)
        except stripe.error.InvalidRequestError:
            print("Creating a new customer...")
            customer = stripe.Customer.create(email="neeraj@gmail.com", name="Neeraj")

        session = stripe.financial_connections.Session.create(
            account_holder={"type": "customer", "customer": customer["id"]},
            permissions=["transactions", "balances"],
        )
        return jsonify({"clientSecret": session["client_secret"]})
    except Exception as e:
        return jsonify(error=str(e)), 403


@stripe_blueprint.route("/api/create_accounts", methods=["POST"])
@jwt_required()
def create_accounts_api():
    new_accounts = request.get_json()
    if len(new_accounts) == 0:
        return jsonify("Failed to Create Accounts: No Accounts Submitted")

    for account in new_accounts:
        upsert(bank_accounts_collection, account)

    return jsonify({"data": new_accounts})


@stripe_blueprint.route("/api/get_accounts/<session_id>")
@jwt_required()
def get_accounts_api(session_id):
    try:
        session = stripe.financial_connections.Session.retrieve(session_id)
        accounts = session["accounts"]
        for account in accounts:
            upsert(stripe_raw_account_data_collection, account)
        return jsonify({"accounts": accounts})
    except Exception as e:
        return jsonify(error=str(e)), 403


@stripe_blueprint.route("/api/subscribe_to_account/<account_id>")
@jwt_required()
def subscribe_to_account_api(account_id):
    try:
        # TODO: Use requests since we cannot list transactions with the Stripe Python client
        headers = {
            "Stripe-Version": "2022-08-01; financial_connections_transactions_beta=v1",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = "features[]=transactions"
        response = requests.post(
            f"https://api.stripe.com/v1/financial_connections/accounts/{account_id}/subscribe",
            headers=headers,
            data=data,
            auth=(STRIPE_API_KEY, ""),
        )
        refresh_status = json.loads(response.text)["transaction_refresh"]["status"]
        return jsonify(str(refresh_status))
    except Exception as e:
        return jsonify(error=str(e)), 403


@stripe_blueprint.route("/api/get_transactions/<account_id>")
@jwt_required()
def get_transactions_api(account_id):
    print(f"Getting Transactions for {account_id}")
    # TODO: This gets all transactions ever. We should only get those that we don't have
    try:
        # TODO: Use requests since we cannot list transactions with the Stripe Python client
        has_more = True
        headers = {
            "Stripe-Version": "2022-08-01; financial_connections_transactions_beta=v1",
        }
        params = {
            "limit": "100",
            "account": account_id,
        }
        while has_more:
            response = requests.get(
                "https://api.stripe.com/v1/financial_connections/transactions",
                params=params,
                headers=headers,
                auth=(STRIPE_API_KEY, ""),
            )
            response = json.loads(response.text)
            data = response["data"]
            for transaction in data:
                if transaction["status"] == "posted":
                    upsert(stripe_raw_transaction_data_collection, transaction)
                elif transaction["status"] == "pending":
                    print(
                        f"Pending Transaction: {transaction['description']} | "
                        + f"{cents_to_dollars(flip_amount(transaction['amount']))}"
                    )
            has_more = response["has_more"]
            last_transaction = data[-1]
            params["starting_after"] = last_transaction["id"]

        stripe_to_line_items()
        return jsonify("Refreshed Stripe Connection for Given Account")

    except Exception as e:
        return jsonify(error=str(e)), 403


def refresh_stripe():
    print("Refreshing Stripe Data")
    bank_accounts = get_all_data(bank_accounts_collection)
    for account in bank_accounts:
        get_transactions_api(account["id"])


def stripe_to_line_items():
    payment_method = "Stripe"
    stripe_raw_data = get_all_data(stripe_raw_transaction_data_collection)
    for transaction in stripe_raw_data:
        transaction_account = get_item_by_id(
            bank_accounts_collection, transaction["account"]
        )
        payment_method = transaction_account["display_name"]
        line_item = LineItem(
            f'line_item_{transaction["_id"]}',
            transaction["transacted_at"],
            transaction["description"],
            payment_method,
            transaction["description"],
            flip_amount(transaction["amount"]) / 100,
        )
        upsert(line_items_collection, line_item)
