import logging
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required
from venmo_api.models.user import User

from clients import get_venmo_client, splitwise_client
from constants import (
    CORS_ALLOWED_ORIGINS,
    DATABASE_HOST,
    DATABASE_NAME,
    DATABASE_PASSWORD,
    DATABASE_USERNAME,
    JWT_COOKIE_DOMAIN,
    JWT_SECRET_KEY,
    LOG_LEVEL,
    SPLITWISE_API_KEY,
    SPLITWISE_CONSUMER_KEY,
    SPLITWISE_CONSUMER_SECRET,
    STRIPE_API_KEY,
    STRIPE_CUSTOMER_ID,
    TESTING,
    VENMO_ACCESS_TOKEN,
)
from dao import (
    bank_accounts_collection,
    get_all_data,
    get_item_by_id,
    users_collection,
)
from resources.auth import auth_blueprint
from resources.category import categories_blueprint
from resources.event import events_blueprint
from resources.event_hint import event_hints_blueprint
from resources.line_item import all_line_items, line_items_blueprint
from resources.manual_transaction import manual_transaction_blueprint
from resources.monthly_breakdown import monthly_breakdown_blueprint
from resources.splitwise import (
    refresh_splitwise,
    splitwise_blueprint,
    splitwise_to_line_items,
)
from resources.stripe import (
    refresh_stripe,
    refresh_transactions_api,
    stripe_blueprint,
    stripe_to_line_items,
)
from resources.tags import tags_blueprint
from resources.venmo import refresh_venmo, venmo_blueprint, venmo_to_line_items

# Configure logging to stdout for cloud compatibility
# Logs are treated as event streams that can be aggregated by cloud platforms
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    force=True,  # Override any existing logging configuration
)

# Create module logger
logger = logging.getLogger(__name__)

# Validate required environment variables before starting app
required_vars = {
    "JWT_SECRET_KEY": JWT_SECRET_KEY,
    "JWT_COOKIE_DOMAIN": JWT_COOKIE_DOMAIN,
    "VENMO_ACCESS_TOKEN": VENMO_ACCESS_TOKEN,
    "SPLITWISE_CONSUMER_KEY": SPLITWISE_CONSUMER_KEY,
    "SPLITWISE_CONSUMER_SECRET": SPLITWISE_CONSUMER_SECRET,
    "SPLITWISE_API_KEY": SPLITWISE_API_KEY,
    "STRIPE_LIVE_API_SECRET_KEY": STRIPE_API_KEY,
    "STRIPE_CUSTOMER_ID": STRIPE_CUSTOMER_ID,
}
# Database credentials required in production (tests use SQLite with defaults)
if not TESTING:
    required_vars.update(
        {
            "DATABASE_HOST": DATABASE_HOST,
            "DATABASE_USERNAME": DATABASE_USERNAME,
            "DATABASE_PASSWORD": DATABASE_PASSWORD,
            "DATABASE_NAME": DATABASE_NAME,
        }
    )
missing = [name for name, value in required_vars.items() if not value]
if missing:
    raise RuntimeError(f"Required environment variables not set: {', '.join(missing)}")

application: Flask = Flask(__name__)

cors: CORS = CORS(
    application,
    supports_credentials=True,
    origins=CORS_ALLOWED_ORIGINS,
    allow_headers=["Content-Type", "Authorization", "X-CSRF-TOKEN"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)
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
application.config["JWT_COOKIE_CSRF_PROTECT"] = True
# Only allow JWT cookies to be sent over https. In production, this
# should likely be True
application.config["JWT_COOKIE_SECURE"] = True

application.register_blueprint(auth_blueprint)
application.register_blueprint(line_items_blueprint)
application.register_blueprint(events_blueprint)
application.register_blueprint(monthly_breakdown_blueprint)
application.register_blueprint(venmo_blueprint)
application.register_blueprint(splitwise_blueprint)
application.register_blueprint(manual_transaction_blueprint)
application.register_blueprint(stripe_blueprint)
application.register_blueprint(tags_blueprint)
application.register_blueprint(event_hints_blueprint)
application.register_blueprint(categories_blueprint)

# If an environment variable is not found in the .env file,
# load_dotenv will then search for a variable by the given name in the host environment.
load_dotenv()


# Register a callback function that loads a user from your database whenever
# a protected route is accessed. This should return any python object on a
# successful lookup, or None if the lookup failed for any reason (for example
# if the user has been deleted from the database).
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header: Dict[str, Any], jwt_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    user_id: str = jwt_data["sub"]
    return get_item_by_id(users_collection, user_id)


@application.route("/api/")
def index_api() -> tuple[Response, int]:
    return jsonify("Welcome to Budgit API"), 200


@application.route("/api/refresh/scheduled")
def schedule_refresh_api() -> tuple[Response, int]:
    logger.info("Initiating scheduled refresh at " + str(datetime.now()))
    try:
        refresh_all()
        create_consistent_line_items()
    except Exception as e:
        logger.error("Error refreshing all: " + str(e))
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "success"}), 200


@application.route("/api/refresh/all", methods=["POST"])
@jwt_required()
def refresh_all_api() -> tuple[Response, int]:
    refresh_all()
    create_consistent_line_items()
    line_items: List[Dict[str, Any]] = all_line_items(only_line_items_to_review=True)
    return jsonify({"data": line_items}), 200


@application.route("/api/refresh/account", methods=["POST"])
@jwt_required()
def refresh_single_account_api() -> tuple[Response, int]:
    """
    Refresh data for a single connected account.

    For Stripe accounts: refreshes transactions for the specific account.
    For Venmo/Splitwise: refreshes all data (user-level integrations).
    """
    try:
        data = request.get_json()
        account_id = data.get("accountId")
        source = data.get("source")

        if not account_id or not source:
            return jsonify({"error": "accountId and source are required"}), 400

        if source == "stripe":
            refresh_transactions_api(account_id)
            stripe_to_line_items()
        elif source == "venmo":
            refresh_venmo()
            venmo_to_line_items()
        elif source == "splitwise":
            refresh_splitwise()
            splitwise_to_line_items()
        else:
            return jsonify({"error": f"Invalid source: {source}"}), 400

        return jsonify({"message": "success"}), 200

    except Exception as e:
        logger.error(f"Error refreshing account {account_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


@application.route("/api/connected_accounts", methods=["GET"])
@jwt_required()
def get_connected_accounts_api() -> tuple[Response, int]:
    connected_accounts: List[Dict[str, Any]] = []
    # # venmo
    profile: User | None = get_venmo_client().my_profile()
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
    """
    Get all payment methods.

    Returns full payment method objects including id, name, type, and is_active.
    """
    from models.database import SessionLocal
    from models.sql_models import PaymentMethod

    db = SessionLocal()
    try:
        payment_methods = db.query(PaymentMethod).filter(PaymentMethod.is_active.is_(True)).all()
        result = [
            {
                "id": pm.id,
                "name": pm.name,
                "type": pm.type,
                "is_active": pm.is_active,
            }
            for pm in payment_methods
        ]
        return jsonify({"data": result}), 200
    finally:
        db.close()


# TODO: Need to add webhooks for updates after the server has started


def refresh_all() -> None:
    logger.info("Refreshing All Data")
    refresh_splitwise()
    refresh_venmo()
    refresh_stripe()


def create_consistent_line_items() -> None:
    logger.info("Creating Consistent Line Items")
    splitwise_to_line_items()
    venmo_to_line_items()
    stripe_to_line_items()
    # Note: Manual transactions don't need refresh - they're created directly when user submits
    logger.info("Created consistent line items")


if __name__ == "__main__":
    application.config["CORS_HEADERS"] = "Content-Type"
    application.config["ENV"] = "development"
    application.config["DEBUG"] = True
    application.config["TESTING"] = True
    application.debug = True
    application.run(host="dev.localhost", port=4242)
