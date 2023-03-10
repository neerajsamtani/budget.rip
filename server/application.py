import os
from dotenv import load_dotenv
from splitwise import Splitwise
from venmo_api import Client
from flask import Flask, jsonify, request
import json
import requests
from line_item import LineItem
import stripe
from flask_cors import CORS, cross_origin
from helpers import *
from constants import *
from dao import *

# Flask constructor takes the name of
# current module (__name__) as argument.
application = Flask(__name__, static_folder='public',
            static_url_path='', template_folder='public')
cors = CORS(application)

session = ""

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

@application.route('/api/')
@cross_origin()
def index():
    application.logger.info("You Hit API Index")
    return jsonify('Welcome to Budgit API')

@application.route('/api/all')
@cross_origin()
def all():
    filters = {}
    filters["event_id"] = { "$exists": False}
    line_items = get_all_data(line_items_db, filters)
    line_items_total = sum(line_item["amount"] for line_item in line_items)
    line_items = sort_by_date(line_items)
    return jsonify({"total":line_items_total, "data": line_items})

@application.route('/api/line_items')
@cross_origin()
def all_line_items():

    filters = {}
    payment_method = request.args.get("payment_method")
    if payment_method not in ["All", None]:
        filters["payment_method"] = payment_method

    line_items = get_all_data(line_items_db, filters)
    line_items_total = sum(line_item["amount"] for line_item in line_items)
    return jsonify({"total":line_items_total, "data": line_items})

@application.route('/api/line_items/<line_item_id>')
@cross_origin()
def get_line_item(line_item_id):
    line_item = get_item_by_id(line_items_db, line_item_id)
    return jsonify(line_item)

@application.route('/api/line_items_for_event/<event_id>')
@cross_origin()
def line_items_for_event(event_id):
    try:
        event = get_item_by_id(events_db, event_id)
        line_items = []
        for line_item_id in event["line_items"]:
            line_items.append(get_item_by_id(line_items_db, line_item_id))
        return jsonify({"data": line_items})
    except Exception as e:
        return jsonify(error=str(e)), 403

@application.route('/api/events')
@cross_origin()
def all_events():
    filters = {}
    category = request.args.get("category")
    month = request.args.get("month")
    if category not in ["All", None]:
        filters["category"] = category
    if month not in ["All", None]:
        month_start, month_end = get_month_date_range(month)
        filters["date"] = { "$gte": month_start, "$lte": month_end}
    events = get_all_data(events_db, filters)
    events_total = sum(event["amount"] for event in events)
    return jsonify({"total":events_total, "data": events})

@application.route('/api/events/<event_id>')
@cross_origin()
def get_event(event_id):
    event = get_item_by_id(events_db, event_id)
    return jsonify(event)

@application.route('/api/create_event', methods=['POST'])
@cross_origin()
def create_event():
    # TODO: This should just be a POST to /api/events
    new_event = request.json
    if len(new_event["line_items"]) == 0:
        return jsonify('Failed to Create Event: No Line Items Submitted')

    filters = {}
    filters["_id"] = { "$in": new_event["line_items"]}
    line_items = get_all_data(line_items_db, filters)
    earliest_line_item = min(line_items, key=lambda line_item: line_item["date"])

    new_event["id"] = f"event{earliest_line_item['id'][9:]}"
    if new_event["date"]:
        new_event["date"] = html_date_to_posix(new_event["date"])
    else:
        new_event["date"] = earliest_line_item["date"]

    if new_event["is_duplicate_transaction"]:
        new_event["amount"] = line_items[0]["amount"]
    else:
        new_event["amount"] = sum(line_item["amount"] for line_item in line_items)

    upsert_with_id(events_db, new_event, new_event["id"])
    for line_item in line_items:
        line_item["event_id"] = new_event["id"]
        upsert(line_items_db, line_item)

    return jsonify('Created Event')

@application.route('/api/delete_event/<event_id>')
@cross_origin()
def delete_event(event_id):
    # TODO: This should just be a delete to /api/events/<event_id>
    try:
        event = get_item_by_id(events_db, event_id)
        line_item_ids = event["line_items"]
        delete_from_db(events_db, event_id)
        for line_item_id in line_item_ids:
            remove_event_from_line_item(line_item_id)
        return jsonify('Deleted Event')
    except Exception as e:
        return jsonify(error=str(e)), 403

@application.route('/api/refresh_venmo')
@cross_origin()
def refresh_venmo(VENMO_ACCESS_TOKEN = os.getenv('VENMO_ACCESS_TOKEN')):
    client = Client(access_token=VENMO_ACCESS_TOKEN)
    my_id = client.my_profile().id
    transactions = client.user.get_user_transactions(my_id)
    transactions_after_moving_date = True
    while transactions and transactions_after_moving_date:
        for transaction in transactions:
            if transaction.date_created < MOVING_DATE_POSIX:
                transactions_after_moving_date = False
                break
            elif transaction.actor.first_name in PARTIES_TO_IGNORE or transaction.target.first_name in PARTIES_TO_IGNORE:
                continue
            upsert(venmo_raw_data_db, transaction)
        transactions = transactions.get_next_page() # TODO: This might have one extra network call when we break out of the loop
    venmo_to_line_items()
    return jsonify('Refreshed Venmo Connection')

@application.route('/api/refresh_splitwise')
@cross_origin()
def refresh_splitwise(SPLITWISE_CONSUMER_KEY = os.getenv('SPLITWISE_CONSUMER_KEY'),
                        SPLITWISE_CONSUMER_SECRET = os.getenv('SPLITWISE_CONSUMER_SECRET'),
                        SPLITWISE_API_KEY = os.getenv('SPLITWISE_API_KEY')):
    sObj = Splitwise(SPLITWISE_CONSUMER_KEY,SPLITWISE_CONSUMER_SECRET,api_key=SPLITWISE_API_KEY)
    expenses = sObj.getExpenses(limit=LIMIT, dated_after=MOVING_DATE)
    for expense in expenses:
        if expense.deleted_at is not None:
            continue
        upsert(splitwise_raw_data_db, expense)
    splitwise_to_line_items()
    return jsonify('Refreshed Splitwise Connection')

@application.route('/api/refresh_stripe')
@cross_origin()
def refresh_stripe():
    accounts = get_all_data(accounts_db)
    for account in accounts:
        get_transactions(account["id"])
    return jsonify('Refreshed Stripe Connection')

@application.route('/api/refresh_data')
@cross_origin()
def refresh_data():
    refresh_splitwise()
    refresh_venmo()
    refresh_stripe()
    create_consistent_line_items()
    return jsonify('Refreshed Data')

@application.route('/api/create_cash_transaction', methods=['POST'])
@cross_origin()
def create_cash_transaction():
    transaction = request.json
    transaction["date"] = html_date_to_posix(transaction["date"])
    transaction["amount"] = int(transaction["amount"])
    insert(cash_raw_data_db, transaction)
    cash_to_line_items()
    return jsonify('Created Cash Transaction')

@application.route('/api/create-fc-session', methods=['POST'])
@cross_origin()
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
        return jsonify({
            'clientSecret': session['client_secret']
        })
    except Exception as e:
        return jsonify(error=str(e)), 403

@application.route('/api/create_accounts', methods=['POST'])
@cross_origin()
def create_accounts():
    new_accounts = request.json
    if len(new_accounts) == 0:
        return jsonify('Failed to Create Accounts: No Accounts Submitted')

    for account in new_accounts:
        upsert(accounts_db, account)

    return jsonify({"data": new_accounts})

@application.route('/api/get_accounts/<session_id>')
@cross_origin()
def get_accounts(session_id):
    try:
        session = stripe.financial_connections.Session.retrieve(session_id)
        accounts = session["accounts"]
        for account in accounts:
            upsert(stripe_raw_account_data_db, account)
        return jsonify({
            'accounts': accounts
        })
    except Exception as e:
        return jsonify(error=str(e)), 403

@application.route('/api/subscribe_to_account/<account_id>')
@cross_origin()
def subscribe_to_account(account_id):
    try:
        # TODO: Use requests since we cannot list transactions with the Stripe Python client
        headers = {
            'Stripe-Version': '2022-08-01; financial_connections_transactions_beta=v1',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = 'features[]=transactions'
        response = requests.post(
            f'https://api.stripe.com/v1/financial_connections/accounts/{account_id}/subscribe',
            headers=headers,
            data=data,
            auth=(STRIPE_API_KEY, ''),
        )
        refresh_status = json.loads(response.text)["transaction_refresh"]["status"]
        return jsonify(str(refresh_status))
    except Exception as e:
        return jsonify(error=str(e)), 403

@application.route('/api/get_transactions/<account_id>')
@cross_origin()
def get_transactions(account_id):
    # TODO: This gets all transactions ever. We should only get those that we don't have
    try:
        # TODO: Use requests since we cannot list transactions with the Stripe Python client
        has_more = True
        headers = {
            'Stripe-Version': '2022-08-01; financial_connections_transactions_beta=v1',
        }
        params = {
            'limit': '100',
            'account': account_id,
        }
        while has_more:
            response = requests.get(
                'https://api.stripe.com/v1/financial_connections/transactions',
                params=params,
                headers=headers,
                auth=(STRIPE_API_KEY, ''),
            )
            response = json.loads(response.text)
            data = response["data"]
            for transaction in data:
                if transaction["status"] == "posted":
                    upsert(stripe_raw_transaction_data_db, transaction)
            has_more = response["has_more"]
            last_transaction = data[-1]
            params["starting_after"] = last_transaction["id"]

        stripe_to_line_items()
        return jsonify('Refreshed Stripe Connection for Given Account')

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
    expenses = get_all_data(splitwise_raw_data_db)
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
            if user["first_name"] != USER_FIRST_NAME: continue
            line_item = LineItem(f'line_item_{expense["_id"]}', posix_date, responsible_party, payment_method, expense["description"], flip_amount(user["net_balance"]))
            upsert(line_items_db, line_item)
            break

def venmo_to_line_items():
    payment_method = "Venmo"
    venmo_raw_data = get_all_data(venmo_raw_data_db)
    for transaction in venmo_raw_data:
        posix_date = float(transaction["date_created"])
        if transaction["actor"]["first_name"] == USER_FIRST_NAME and transaction["payment_type"] == "pay":
            # current user paid money
            line_item = LineItem(f'line_item_{transaction["_id"]}', posix_date, transaction["target"]["first_name"], payment_method, transaction["note"], transaction["amount"])
        elif transaction["target"]["first_name"] == USER_FIRST_NAME and transaction["payment_type"] == "charge":
            # current user paid money
            line_item = LineItem(f'line_item_{transaction["_id"]}', posix_date, transaction["actor"]["first_name"], payment_method, transaction["note"], transaction["amount"])
        else:
            # current user gets money
            if transaction["target"]["first_name"] == USER_FIRST_NAME:
                other_name = transaction["actor"]["first_name"]
            else:
                other_name = transaction["target"]["first_name"]
            line_item = LineItem(f'line_item_{transaction["_id"]}', posix_date, other_name, payment_method, transaction["note"], flip_amount(transaction["amount"]))
        upsert(line_items_db, line_item)

def stripe_to_line_items():
    payment_method = "Stripe"
    stripe_raw_data = get_all_data(stripe_raw_transaction_data_db)
    for transaction in stripe_raw_data:
        line_item = LineItem(f'line_item_{transaction["_id"]}', transaction["transacted_at"], transaction["description"], payment_method, transaction["description"], flip_amount(transaction["amount"]) / 100)
        upsert(line_items_db, line_item)

def cash_to_line_items():
    payment_method = "Cash"
    cash_raw_data = get_all_data(cash_raw_data_db)
    for transaction in cash_raw_data:
        line_item = LineItem(f'line_item_{transaction["_id"]}', transaction["date"], transaction["person"], payment_method, transaction["description"], transaction["amount"])
        upsert(line_items_db, line_item)

def add_event_ids_to_line_items():
    events = get_all_data(events_db)
    for event in events:

        filters = {}
        filters["_id"] = { "$in": event["line_items"]}
        line_items = get_all_data(line_items_db, filters)

        for line_item in line_items:
            line_item["event_id"] = event["id"]
            upsert(line_items_db, line_item)

def create_consistent_line_items():
    splitwise_to_line_items()
    venmo_to_line_items()
    stripe_to_line_items()
    cash_to_line_items()
    add_event_ids_to_line_items()

# main driver function
if __name__ == '__main__':
    # run() method of Flask class runs the application
    # on the local development server.
    create_consistent_line_items()
    # TODO: Disable debugging
    application.config['CORS_HEADERS'] = 'Content-Type'
    application.config['ENV'] = 'development'
    application.config['DEBUG'] = True
    application.config['TESTING'] = True
    application.debug = True
    application.run(port=4242)
