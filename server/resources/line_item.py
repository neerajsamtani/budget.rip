import json
import logging
from typing import Any, Dict, List, Optional

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required

from dao import get_all_line_items, get_line_item_by_id, update_line_item
from helpers import sort_by_date_amount_descending, str_to_bool

logger = logging.getLogger(__name__)

line_items_blueprint = Blueprint("line_items", __name__)

# TODO: Exceptions


class LineItem:
    """
    Line item data transfer object.

    Fields:
        source_id: External API transaction ID (e.g., Venmo's ID). Used during creation
                   to link line items to their source transactions.
        transaction_id: Database transaction foreign key (txn_xxx). Populated after
                       line items are inserted into the database.
    """

    def __init__(
        self,
        date: float,
        responsible_party: str,
        payment_method: str,
        description: str,
        amount: float,
        id: str = "",
        source_id: str = "",
        transaction_id: str = "",
    ) -> None:
        self.id = id
        self.date = date
        self.responsible_party = responsible_party
        self.payment_method = payment_method
        self.description = description
        self.amount = amount
        self.source_id = source_id  # External API ID (e.g., Venmo's transaction ID)
        self.transaction_id = transaction_id  # Database transaction FK (e.g., txn_abc123)

    def serialize(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date,
            "responsible_party": self.responsible_party,
            "payment_method": self.payment_method,
            "description": self.description,
            "amount": self.amount,
        }

    def __repr__(self) -> str:
        return f"""{{
        id: {self.id}
        date: {self.date}
        responsible_party: {self.responsible_party}
        payment_method: {self.payment_method}
        description: {self.description}
        amount: {self.amount}
        }}
        """

    def to_json(self) -> str:
        """
        convert the instance of this class to json
        """
        return json.dumps(self, indent=4, default=lambda o: o.__dict__)


@line_items_blueprint.route("/api/line_items", methods=["GET"])
@jwt_required()
def all_line_items_api() -> tuple[Response, int]:
    """
    Get All Line Items
        - Payment Method (optional)
        - Only Line Items To Review (optional)
    """
    only_line_items_to_review: Optional[bool] = str_to_bool(request.args.get("only_line_items_to_review"))
    payment_method: Optional[str] = request.args.get("payment_method")
    line_items: List[Dict[str, Any]] = all_line_items(only_line_items_to_review, payment_method)
    line_items_total: float = sum(line_item["amount"] for line_item in line_items)
    logger.info(f"Retrieved {len(line_items)} line items (total: ${line_items_total:.2f})")
    return jsonify({"total": line_items_total, "data": line_items}), 200


def all_line_items(
    only_line_items_to_review: Optional[bool] = None,
    payment_method: Optional[str] = None,
) -> List[Dict[str, Any]]:
    filters: Dict[str, Any] = {}
    if payment_method not in ["All", None]:
        filters["payment_method"] = payment_method

    if only_line_items_to_review:
        # Only get line items that don't have an event associated
        filters["event_id"] = {"$exists": False}

    line_items: List[Dict[str, Any]] = get_all_line_items(filters)
    line_items = sort_by_date_amount_descending(line_items)
    return line_items


@line_items_blueprint.route("/api/line_items/<line_item_id>", methods=["GET"])
@jwt_required()
def get_line_item_api(line_item_id: str) -> tuple[Response, int]:
    """
    Get A Line Item
    """
    line_item: Optional[Dict[str, Any]] = get_line_item_by_id(line_item_id)
    if line_item is None:
        logger.warning(f"Line item not found: {line_item_id}")
        return jsonify({"error": "Line item not found"}), 404
    logger.info(f"Retrieved line item: {line_item_id}")
    return jsonify(line_item), 200


@line_items_blueprint.route("/api/line_items/<line_item_id>", methods=["PATCH"])
@jwt_required()
def update_line_item_api(line_item_id: str) -> tuple[Response, int]:
    """
    Update a line item's editable fields.
    Currently supports: notes
    """
    update_data: Dict[str, Any] = request.get_json()

    allowed_fields = {"notes"}
    invalid_fields = set(update_data.keys()) - allowed_fields
    if invalid_fields:
        logger.warning(f"Line item update attempt with invalid fields: {invalid_fields}")
        return jsonify({"error": f"Invalid fields: {', '.join(invalid_fields)}"}), 400

    updated_line_item = update_line_item(line_item_id, update_data)

    if updated_line_item is None:
        logger.warning(f"Line item update attempt for non-existent item: {line_item_id}")
        return jsonify({"error": "Line item not found"}), 404

    logger.info(f"Updated line item: {line_item_id}")
    return jsonify({"data": updated_line_item, "message": "Line item updated"}), 200
