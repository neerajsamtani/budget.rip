from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from clients import splitwise_client, venmo_client
from constants import *
from dao import *
from helpers import *
from resources.cash import cash_blueprint, cash_to_line_items
from resources.event import events_blueprint
from resources.line_item import all_line_items, line_items_blueprint
from resources.monthly_breakdown import monthly_breakdown_blueprint
from resources.splitwise import (
    refresh_splitwise,
    splitwise_blueprint,
    splitwise_to_line_items,
)
from resources.stripe import refresh_stripe, stripe_blueprint, stripe_to_line_items
from resources.venmo import refresh_venmo, venmo_blueprint, venmo_to_line_items

# Flask constructor takes the name of
# current module (__name__) as argument.
application = Flask(
    __name__, static_folder="public", static_url_path="", template_folder="public"
)
application.register_blueprint(line_items_blueprint)
application.register_blueprint(events_blueprint)
application.register_blueprint(monthly_breakdown_blueprint)
application.register_blueprint(venmo_blueprint)
application.register_blueprint(splitwise_blueprint)
application.register_blueprint(cash_blueprint)
application.register_blueprint(stripe_blueprint)
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


# TODO: Integrate with Splitwise OAuth to enable other people to use this without submitting API Keys
# https://blog.splitwise.com/2013/07/15/setting-up-oauth-for-the-splitwise-api/

# TODO: Need to add webhooks for updates after the server has started


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
