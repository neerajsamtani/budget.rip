import json
import os
from collections import defaultdict

import requests
import stripe
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from splitwise import Splitwise
from venmo_api import Client

from constants import *
from dao import *
from helpers import *
from line_item import LineItem
from resources.event import events
from resources.line_item import line_items

# Flask constructor takes the name of
# current module (__name__) as argument.
application = Flask(
    __name__, static_folder="public", static_url_path="", template_folder="public"
)
application.register_blueprint(line_items)
application.register_blueprint(events)
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
    application.logger.info("You Hit API Index")
    return jsonify("Welcome to Budgit API")


@application.route("/api/monthly_breakdown")
def monthly_breakdown():
    """
    Get Monthly Breakdown For Plotly Graph
    """
    categorized_data = get_categorized_data()
    categories = defaultdict(empty_list)
    seen_dates = set()
    for row in categorized_data:
        category = row["category"]
        formatted_date = f"{row['month']}-{row['year']}"
        seen_dates.add(formatted_date)
        categories[category].append(
            {"date": formatted_date, "amount": row["totalExpense"]}
        )
    # Ensure no categories have missing dates
    for category, info in categories.items():
        unseen_dates = seen_dates.difference([x["date"] for x in info])
        info.extend([{"date": x, "amount": 0.0} for x in unseen_dates])
        info.sort(key=lambda x: datetime.strptime(x["date"], "%m-%Y").date())
    return categories


@application.route("/api/refresh_venmo")
def refresh_venmo(VENMO_ACCESS_TOKEN=os.getenv("VENMO_ACCESS_TOKEN")):
    venmo_client = Client(access_token=VENMO_ACCESS_TOKEN)
    my_id = venmo_client.my_profile().id
    transactions = venmo_client.user.get_user_transactions(my_id)
    transactions_after_moving_date = True
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
            upsert(venmo_raw_data_collection, transaction)
        transactions = (
            transactions.get_next_page()
        )  # TODO: This might have one extra network call when we break out of the loop
    venmo_to_line_items()
    return jsonify("Refreshed Venmo Connection")


@application.route("/api/refresh_splitwise")
def refresh_splitwise(
    SPLITWISE_CONSUMER_KEY=os.getenv("SPLITWISE_CONSUMER_KEY"),
    SPLITWISE_CONSUMER_SECRET=os.getenv("SPLITWISE_CONSUMER_SECRET"),
    SPLITWISE_API_KEY=os.getenv("SPLITWISE_API_KEY"),
):
    sObj = Splitwise(
        SPLITWISE_CONSUMER_KEY, SPLITWISE_CONSUMER_SECRET, api_key=SPLITWISE_API_KEY
    )
    expenses = sObj.getExpenses(limit=LIMIT, dated_after=MOVING_DATE)
    for expense in expenses:
        if expense.deleted_at is not None:
            continue
        upsert(splitwise_raw_data_collection, expense)
    splitwise_to_line_items()
    return jsonify("Refreshed Splitwise Connection")


@application.route("/api/refresh_stripe")
def refresh_stripe():
    bank_accounts = get_all_data(bank_accounts_collection)
    for account in bank_accounts:
        get_transactions(account["id"])
    return jsonify("Refreshed Stripe Connection")


@application.route("/api/connected_accounts", methods=["GET"])
def get_connected_accounts():
    connected_accounts = []
    # venmo
    venmo_client = Client(access_token=os.getenv("VENMO_ACCESS_TOKEN"))
    connected_accounts.append(f"{venmo_client.my_profile().username} (venmo)")
    # splitwise
    sObj = Splitwise(
        os.getenv("SPLITWISE_CONSUMER_KEY"),
        os.getenv("SPLITWISE_CONSUMER_SECRET"),
        api_key=os.getenv("SPLITWISE_API_KEY"),
    )
    connected_accounts.append(
        f"{sObj.getCurrentUser().getFirstName()} {sObj.getCurrentUser().getLastName()} (splitwise)"
    )
    # stripe
    bank_accounts = get_all_data(bank_accounts_collection)
    for account in bank_accounts:
        connected_accounts.append(
            f"{account['display_name']} {account['last4']} (stripe)"
        )
    return jsonify(connected_accounts)


@application.route("/api/refresh_data")
def refresh_data():
    refresh_splitwise()
    refresh_venmo()
    refresh_stripe()
    create_consistent_line_items()
    return all_line_items(local_only_line_items_to_review=True)


@application.route("/api/create_cash_transaction", methods=["POST"])
def create_cash_transaction():
    transaction = request.json
    transaction["date"] = html_date_to_posix(transaction["date"])
    transaction["amount"] = int(transaction["amount"])
    insert(cash_raw_data_collection, transaction)
    cash_to_line_items()
    return jsonify("Created Cash Transaction")


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


def splitwise_to_line_items():
    payment_method = "Splitwise"
    expenses = get_all_data(splitwise_raw_data_collection)
    for expense in expenses:
        responsible_party = ""
        # Get Person Name
        for user in expense["users"]:
            if user["first_name"] != USER_FIRST_NAME:
                # TODO: Set up comma separated list of responsible parties
                responsible_party += f'{user["first_name"]} '
        if responsible_party in PARTIES_TO_IGNORE:
            continue
        posix_date = iso_8601_to_posix(expense["date"])
        for user in expense["users"]:
            if user["first_name"] != USER_FIRST_NAME:
                continue
            line_item = LineItem(
                f'line_item_{expense["_id"]}',
                posix_date,
                responsible_party,
                payment_method,
                expense["description"],
                flip_amount(user["net_balance"]),
            )
            upsert(line_items_collection, line_item)
            break


def venmo_to_line_items():
    payment_method = "Venmo"
    venmo_raw_data = get_all_data(venmo_raw_data_collection)
    for transaction in venmo_raw_data:
        posix_date = float(transaction["date_created"])
        if (
            transaction["actor"]["first_name"] == USER_FIRST_NAME
            and transaction["payment_type"] == "pay"
        ):
            # current user paid money
            line_item = LineItem(
                f'line_item_{transaction["_id"]}',
                posix_date,
                transaction["target"]["first_name"],
                payment_method,
                transaction["note"],
                transaction["amount"],
            )
        elif (
            transaction["target"]["first_name"] == USER_FIRST_NAME
            and transaction["payment_type"] == "charge"
        ):
            # current user paid money
            line_item = LineItem(
                f'line_item_{transaction["_id"]}',
                posix_date,
                transaction["actor"]["first_name"],
                payment_method,
                transaction["note"],
                transaction["amount"],
            )
        else:
            # current user gets money
            if transaction["target"]["first_name"] == USER_FIRST_NAME:
                other_name = transaction["actor"]["first_name"]
            else:
                other_name = transaction["target"]["first_name"]
            line_item = LineItem(
                f'line_item_{transaction["_id"]}',
                posix_date,
                other_name,
                payment_method,
                transaction["note"],
                flip_amount(transaction["amount"]),
            )
        upsert(line_items_collection, line_item)


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


def cash_to_line_items():
    payment_method = "Cash"
    cash_raw_data = get_all_data(cash_raw_data_collection)
    for transaction in cash_raw_data:
        line_item = LineItem(
            f'line_item_{transaction["_id"]}',
            transaction["date"],
            transaction["person"],
            payment_method,
            transaction["description"],
            transaction["amount"],
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
