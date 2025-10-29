import logging
from typing import Any, Dict, List, Optional

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required

from resources.cash import cash_to_line_items
from resources.line_item import all_line_items
from resources.splitwise import refresh_splitwise, splitwise_to_line_items
from resources.stripe import refresh_account_api, refresh_transactions_api, stripe_to_line_items
from resources.venmo import refresh_venmo, venmo_to_line_items

account_blueprint = Blueprint("account", __name__)


@account_blueprint.route("/api/account/<account_type>/refresh", methods=["GET"])
@jwt_required()
def refresh_account_by_type_api(account_type: str) -> tuple[Response, int]:
    """
    Refresh a single account by type (venmo or splitwise).

    Routes:
    - /api/account/venmo/refresh - Refresh Venmo account
    - /api/account/splitwise/refresh - Refresh Splitwise account
    """
    try:
        logging.info(f"Refreshing account type: {account_type}")

        if account_type == "venmo":
            refresh_venmo()
            venmo_to_line_items()
        elif account_type == "splitwise":
            refresh_splitwise()
            splitwise_to_line_items()
        else:
            return (
                jsonify(
                    {
                        "error": f"Invalid account type: {account_type}. Use 'venmo' or 'splitwise'."
                    }
                ),
                400,
            )

        # Import here to avoid circular dependency
        from application import add_event_ids_to_line_items

        # Ensure consistent line items and event associations
        cash_to_line_items()
        add_event_ids_to_line_items()

        # Return all line items
        line_items: List[Dict[str, Any]] = all_line_items(
            only_line_items_to_review=True
        )
        return jsonify({"data": line_items}), 200

    except Exception as e:
        logging.error(f"Error refreshing account type {account_type}: {str(e)}")
        return jsonify({"error": str(e)}), 500


@account_blueprint.route(
    "/api/account/stripe/<account_id>/refresh", methods=["GET"]
)
@jwt_required()
def refresh_stripe_account_api(account_id: str) -> tuple[Response, int]:
    """
    Refresh a specific Stripe bank account.

    Route:
    - /api/account/stripe/<account_id>/refresh - Refresh specific Stripe bank account
    """
    try:
        logging.info(f"Refreshing Stripe account: {account_id}")

        # Refresh specific Stripe account
        refresh_account_api(account_id)
        refresh_transactions_api(account_id)
        stripe_to_line_items()

        # Import here to avoid circular dependency
        from application import add_event_ids_to_line_items

        # Ensure consistent line items and event associations
        cash_to_line_items()
        add_event_ids_to_line_items()

        # Return all line items
        line_items: List[Dict[str, Any]] = all_line_items(
            only_line_items_to_review=True
        )
        return jsonify({"data": line_items}), 200

    except Exception as e:
        logging.error(f"Error refreshing Stripe account {account_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500
