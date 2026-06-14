import logging
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required
from venmo_api.models.user import User

from clients import get_venmo_client
from constants import MOVING_DATE_POSIX, PARTIES_TO_IGNORE, USER_FIRST_NAME
from helpers import flip_amount
from models.database import SessionLocal
from queries import get_transactions
from resources.line_item import LineItem
from utils.integrations import DataSourceIntegration
from utils.pg_bulk_ops import bulk_upsert_transactions

logger = logging.getLogger(__name__)

venmo_blueprint = Blueprint("venmo", __name__)


# TODO: Can I remove MOVING_DATE_POSIX
# TODO: Can I remove PARTIES_TO_IGNORE


class VenmoIntegration(DataSourceIntegration):
    """Venmo-specific fetch and field mapping for the shared integration pipeline."""

    source_name = "venmo_api"

    def fetch_and_store(self) -> None:
        logger.info("Refreshing Venmo Data")
        profile: User | None = get_venmo_client().my_profile()
        if profile is None:
            logger.error("Failed to get Venmo profile")
            raise Exception("Failed to get Venmo profile")
        my_id: int = profile.id
        transactions: Any = get_venmo_client().user.get_user_transactions(str(my_id))  # type: ignore
        transactions_after_moving_date: bool = True

        # Collect all transactions for bulk upsert
        all_transactions: List[Any] = []

        while transactions and transactions_after_moving_date:
            for transaction in transactions:
                if transaction.date_created < MOVING_DATE_POSIX:
                    transactions_after_moving_date = False
                    break
                elif transaction.actor.first_name in PARTIES_TO_IGNORE or transaction.target.first_name in PARTIES_TO_IGNORE:
                    continue
                all_transactions.append(transaction)
            transactions = (
                transactions.get_next_page()
            )  # TODO: This might have one extra network call when we break out of the loop

        # Bulk upsert all collected transactions at once
        if all_transactions:
            with SessionLocal.begin() as db:
                bulk_upsert_transactions(db, all_transactions, source=self.source_name)
            logger.info(f"Refreshed {len(all_transactions)} Venmo transactions")
        else:
            logger.info("No new Venmo transactions to refresh")

    def transactions_to_line_items(self, transactions: List[Dict[str, Any]]) -> List[LineItem]:
        payment_method = "Venmo"
        line_items: List[LineItem] = []
        for venmo_transaction in transactions:
            posix_date = float(venmo_transaction["date_created"])
            actor_name = venmo_transaction["actor"]["first_name"]
            target_name = venmo_transaction["target"]["first_name"]
            payment_type = venmo_transaction["payment_type"]

            if actor_name == USER_FIRST_NAME and payment_type == "pay":
                # current user paid money
                line_items.append(
                    LineItem(
                        posix_date,
                        target_name,
                        payment_method,
                        venmo_transaction["note"],
                        venmo_transaction["amount"],
                        source_id=str(venmo_transaction["source_id"]),
                    )
                )
            elif target_name == USER_FIRST_NAME and payment_type == "charge":
                # current user paid money
                line_items.append(
                    LineItem(
                        posix_date,
                        actor_name,
                        payment_method,
                        venmo_transaction["note"],
                        venmo_transaction["amount"],
                        source_id=str(venmo_transaction["source_id"]),
                    )
                )
            else:
                # current user gets money
                other_name = actor_name if target_name == USER_FIRST_NAME else target_name
                line_items.append(
                    LineItem(
                        posix_date,
                        other_name,
                        payment_method,
                        venmo_transaction["note"],
                        flip_amount(venmo_transaction["amount"]),
                        source_id=str(venmo_transaction["source_id"]),
                    )
                )
        return line_items


@venmo_blueprint.route("/api/refresh/venmo")
@jwt_required()
def refresh_venmo_api() -> tuple[Response, int]:
    try:
        refresh_venmo()
        venmo_to_line_items()
        return jsonify("Refreshed Venmo Connection"), 200
    except Exception as e:
        logger.error(f"Venmo refresh failed: {e}", exc_info=True)
        return jsonify({"error": "Venmo refresh failed"}), 500


def refresh_venmo() -> None:
    VenmoIntegration().fetch_and_store()


def venmo_to_line_items() -> None:
    VenmoIntegration().upsert_line_items(get_transactions("venmo_api", None))
