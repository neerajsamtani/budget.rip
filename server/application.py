import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, Response, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required
from flask_pymongo import PyMongo
from venmo_api.models.user import User

from clients import splitwise_client, venmo_client
from constants import JWT_COOKIE_DOMAIN, JWT_SECRET_KEY, MONGO_URI
from dao import (
    bank_accounts_collection,
    bulk_upsert,
    events_collection,
    get_all_data,
    get_item_by_id,
    line_items_collection,
    users_collection,
)
from resources.auth import auth_blueprint
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
application: Flask = Flask(
    __name__, static_folder="public", static_url_path="", template_folder="public"
)

cors: CORS = CORS(application, supports_credentials=True)
bcrypt: Bcrypt = Bcrypt(application)
jwt: JWTManager = JWTManager(application)
# JWT Config Links
# - https://flask-jwt-extended.readthedocs.io/en/stable/options.html
# - https://flask-jwt-extended.readthedocs.io/en/3.0.0_release/tokens_in_cookies/
application.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
application.config["JWT_COOKIE_DOMAIN"] = JWT_COOKIE_DOMAIN
application.config["JWT_TOKEN_LOCATION"] = ["cookies"]
application.config["JWT_ACCESS_COOKIE_PATH"] = "/api/"
application.config["JWT_COOKIE_SAMESITE"] = "None"
application.config["JWT_COOKIE_CSRF_PROTECT"] = False
# Only allow JWT cookies to be sent over https. In production, this
# should likely be True
application.config["JWT_COOKIE_SECURE"] = True

application.config["MONGO_URI"] = MONGO_URI
application.config["MONGO"] = PyMongo(application)

# Configure the log level (use 'DEBUG' during development and 'INFO' or 'WARNING' in production)
application.logger.setLevel(logging.DEBUG)

application.register_blueprint(auth_blueprint)
application.register_blueprint(line_items_blueprint)
application.register_blueprint(events_blueprint)
application.register_blueprint(monthly_breakdown_blueprint)
application.register_blueprint(venmo_blueprint)
application.register_blueprint(splitwise_blueprint)
application.register_blueprint(cash_blueprint)
application.register_blueprint(stripe_blueprint)

# If an environment variable is not found in the .env file,
# load_dotenv will then search for a variable by the given name in the host environment.
load_dotenv()

# TODO: Add IDs to line items since dates aren't finegrained in python 3.8 datetime

# Get Debug Logging
# logging.basicConfig(level=logging.DEBUG)

# TODO: Type hints


# Register a callback function that loads a user from your database whenever
# a protected route is accessed. This should return any python object on a
# successful lookup, or None if the lookup failed for any reason (for example
# if the user has been deleted from the database).
@jwt.user_lookup_loader
def user_lookup_callback(
    _jwt_header: Dict[str, Any], jwt_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    id: ObjectId = ObjectId(jwt_data["sub"])
    return get_item_by_id(users_collection, id)


##############
### ROUTES ###
##############


@application.route("/api/")
def index_api() -> tuple[Response, int]:
    return jsonify("Welcome to Budgit API"), 200


@application.route("/api/refresh/scheduled")
def schedule_refresh_api() -> tuple[Response, int]:
    print("Initiating scheduled refresh at " + str(datetime.now()))
    try:
        refresh_all()
        create_consistent_line_items()
    except Exception as e:
        print("Error refreshing all: " + str(e))
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "success"}), 200


@application.route("/api/refresh/all")
@jwt_required()
def refresh_all_api() -> tuple[Response, int]:
    refresh_all()
    create_consistent_line_items()
    line_items: List[Dict[str, Any]] = all_line_items(only_line_items_to_review=True)
    return jsonify({"data": line_items}), 200


@application.route("/api/connected_accounts", methods=["GET"])
@jwt_required()
def get_connected_accounts_api() -> tuple[Response, int]:
    connected_accounts: List[Dict[str, Any]] = []
    # # venmo
    profile: User | None = venmo_client.my_profile()
    if profile is None:
        raise Exception("Failed to get Venmo profile")
    connected_accounts.append({"venmo": [profile.username]})
    # splitwise
    connected_accounts.append(
        {
            "splitwise": [
                f"{splitwise_client.getCurrentUser().getFirstName()} {splitwise_client.getCurrentUser().getLastName()}"
            ]
        }
    )
    # stripe
    bank_accounts: List[Dict[str, Any]] = get_all_data(bank_accounts_collection)
    connected_accounts.append({"stripe": bank_accounts})
    return jsonify(connected_accounts), 200


@application.route("/api/payment_methods", methods=["GET"])
@jwt_required()
def get_payment_methods_api() -> tuple[Response, int]:
    # Cash, Venmo, and Splitwise must be connected
    payment_methods: List[str] = ["Cash", "Venmo", "Splitwise"]
    # stripe
    bank_accounts: List[Dict[str, Any]] = get_all_data(bank_accounts_collection)
    for account in bank_accounts:
        payment_methods.append(account["display_name"])
    return jsonify(payment_methods), 200


# TODO: Need to add webhooks for updates after the server has started


def add_event_ids_to_line_items() -> None:
    """
    Add event IDs to line items with optimized database operations.

    Optimizations:
    1. Use bulk upsert operations instead of individual upserts
    2. Collect all line items before bulk upserting
    3. Process line items in batches for better memory management
    """
    events: List[Dict[str, Any]] = get_all_data(events_collection)

    # Collect all line items that need updating for bulk upsert
    all_line_items_to_update: List[Dict[str, Any]] = []

    for event in events:
        filters: Dict[str, Any] = {}
        filters["_id"] = {"$in": event["line_items"]}
        line_items: List[Dict[str, Any]] = get_all_data(line_items_collection, filters)

        for line_item in line_items:
            line_item["event_id"] = event["id"]
            all_line_items_to_update.append(line_item)

    # Bulk upsert all collected line items at once
    if all_line_items_to_update:
        bulk_upsert(line_items_collection, all_line_items_to_update)


def refresh_all() -> None:
    print("Refreshing All Data")
    refresh_splitwise()
    refresh_venmo()
    refresh_stripe()


def create_consistent_line_items() -> None:
    print("Creating Consistent Line Items")
    splitwise_to_line_items()
    venmo_to_line_items()
    stripe_to_line_items()
    cash_to_line_items()
    add_event_ids_to_line_items()
    application.logger.info("Created consistent line items")


# main driver function
if __name__ == "__main__":
    # run() method of Flask class runs the application
    # on the local development server.
    # TODO: Disable debugging
    application.config["CORS_HEADERS"] = "Content-Type"
    application.config["ENV"] = "development"
    application.config["DEBUG"] = True
    application.config["TESTING"] = True
    application.debug = True
    application.run(host="dev.localhost", port=4242)
