import json

import requests
import stripe
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from constants import *
from dao import *
from helpers import *
from line_item import LineItem
from resources.cash import cash, cash_to_line_items
from resources.event import events
from resources.line_item import all_line_items, line_items
from resources.monthly_breakdown import monthly_breakdown
from resources.splitwise import (
    refresh_splitwise,
    splitwise,
    splitwise_client,
    splitwise_to_line_items,
)
from resources.venmo import refresh_venmo, venmo, venmo_client, venmo_to_line_items

# Flask constructor takes the name of
# current module (__name__) as argument.
application = Flask(
    __name__, static_folder="public", static_url_path="", template_folder="public"
)
application.register_blueprint(line_items)
application.register_blueprint(events)
application.register_blueprint(monthly_breakdown)
application.register_blueprint(venmo)
application.register_blueprint(splitwise)
application.register_blueprint(cash)
CORS(application)

# If an environment variable is not found in the .env file,
# load_dotenv will then search for a variable by the given name in the host environment.
load_dotenv()

# TODO: Add IDs to line items since dates aren't finegrained in python 3.8 datetime

# Get Debug Logging
# logging.basicConfig(level=logging.DEBUG)

# TODO: Type hints

##############
### ROUTES ###
##############


@application.route("/api/")
def index():
    return jsonify("Welcome to Budgit API")


@application.route("/api/refresh/stripe")
def refresh_stripe():
    bank_accounts = get_all_data(bank_accounts_collection)
    for account in bank_accounts:
        get_transactions(account["id"])
    return jsonify("Refreshed Stripe Connection")


@application.route("/api/refresh/all")
def refresh_all():
    refresh_splitwise()
    refresh_venmo()
    refresh_stripe()
    create_consistent_line_items()
    return all_line_items(local_only_line_items_to_review=True)


@application.route("/api/connected_accounts", methods=["GET"])
def get_connected_accounts():
    connected_accounts = []
    # venmo
    connected_accounts.append(f"{venmo_client.my_profile().username} (venmo)")
    # splitwise
    connected_accounts.append(
        f"{splitwise_client.getCurrentUser().getFirstName()} {splitwise_client.getCurrentUser().getLastName()} (splitwise)"
    )
    # stripe
    bank_accounts = get_all_data(bank_accounts_collection)
    for account in bank_accounts:
        connected_accounts.append(
            f"{account['display_name']} {account['last4']} (stripe)"
        )
    return jsonify(connected_accounts)


@application.route("/api/create-fc-session", methods=["POST"])
def create_fc_session():
    try:
        # TODO: Is there a better pattern than nested trys?
        try:
            customer = stripe.Customer.retrieve(STRIPE_CUSTOMER_ID)
        except stripe.error.InvalidRequestError as e:
            print("Creating a new customer...")
            customer = stripe.Customer.create(email="neeraj@gmail.com", name="Neeraj")

        session = stripe.financial_connections.Session.create(
            account_holder={"type": "customer", "customer": customer["id"]},
            permissions=["transactions"],
        )
        return jsonify({"clientSecret": session["client_secret"]})
    except Exception as e:
        return jsonify(error=str(e)), 403


@application.route("/api/create_accounts", methods=["POST"])
def create_accounts():
    new_accounts = request.json
    if len(new_accounts) == 0:
        return jsonify("Failed to Create Accounts: No Accounts Submitted")

    for account in new_accounts:
        upsert(bank_accounts_collection, account)

    return jsonify({"data": new_accounts})


@application.route("/api/get_accounts/<session_id>")
def get_accounts(session_id):
    try:
        session = stripe.financial_connections.Session.retrieve(session_id)
        accounts = session["accounts"]
        for account in accounts:
            upsert(stripe_raw_account_data_collection, account)
        return jsonify({"accounts": accounts})
    except Exception as e:
        return jsonify(error=str(e)), 403


@application.route("/api/subscribe_to_account/<account_id>")
def subscribe_to_account(account_id):
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


@application.route("/api/get_transactions/<account_id>")
def get_transactions(account_id):
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
            has_more = response["has_more"]
            last_transaction = data[-1]
            params["starting_after"] = last_transaction["id"]

        stripe_to_line_items()
        return jsonify("Refreshed Stripe Connection for Given Account")

    except Exception as e:
        return jsonify(error=str(e)), 403


# TODO: Integrate everything with OAuth to enable other people to use this
# https://blog.splitwise.com/2013/07/15/setting-up-oauth-for-the-splitwise-api/

########################
### CLEAN LINE ITEMS ###
########################

# TODO: Need to add webhooks for updates after the server has started


def stripe_to_line_items():
    payment_method = "Stripe"
    stripe_raw_data = get_all_data(stripe_raw_transaction_data_collection)
    for transaction in stripe_raw_data:
        line_item = LineItem(
            f'line_item_{transaction["_id"]}',
            transaction["transacted_at"],
            transaction["description"],
            payment_method,
            transaction["description"],
            flip_amount(transaction["amount"]) / 100,
        )
        upsert(line_items_collection, line_item)


def add_event_ids_to_line_items():
    events = get_all_data(events_collection)
    for event in events:
        filters = {}
        filters["_id"] = {"$in": event["line_items"]}
        line_items = get_all_data(line_items_collection, filters)

        for line_item in line_items:
            line_item["event_id"] = event["id"]
            upsert(line_items_collection, line_item)


def create_consistent_line_items():
    splitwise_to_line_items()
    venmo_to_line_items()
    stripe_to_line_items()
    cash_to_line_items()
    add_event_ids_to_line_items()


# main driver function
if __name__ == "__main__":
    # run() method of Flask class runs the application
    # on the local development server.
    create_consistent_line_items()
    # TODO: Disable debugging
    application.config["CORS_HEADERS"] = "Content-Type"
    application.config["ENV"] = "development"
    application.config["DEBUG"] = True
    application.config["TESTING"] = True
    application.debug = True
    application.run(port=4242)
