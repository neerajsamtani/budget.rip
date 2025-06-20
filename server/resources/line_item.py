import json
from typing import Any, Dict, List, Optional

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required

from dao import get_all_data, get_item_by_id, line_items_collection
from helpers import sort_by_date_descending, str_to_bool

line_items_blueprint = Blueprint("line_items", __name__)

# TODO: Exceptions


class LineItem:
    def __init__(
        self,
        id: str,
        date: float,
        responsible_party: str,
        payment_method: str,
        description: str,
        amount: float,
    ) -> None:
        self.id = id
        self.date = date
        self.responsible_party = responsible_party
        self.payment_method = payment_method
        self.description = description
        self.amount = amount

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
    only_line_items_to_review: Optional[bool] = str_to_bool(
        request.args.get("only_line_items_to_review")
    )
    payment_method: Optional[str] = request.args.get("payment_method")
    line_items: List[Dict[str, Any]] = all_line_items(
        only_line_items_to_review, payment_method
    )
    line_items_total: float = sum(line_item["amount"] for line_item in line_items)
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

    line_items: List[Dict[str, Any]] = get_all_data(line_items_collection, filters)
    line_items = sort_by_date_descending(line_items)
    return line_items


@line_items_blueprint.route("/api/line_items/<line_item_id>", methods=["GET"])
def get_line_item_api(line_item_id: str) -> tuple[Response, int]:
    """
    Get A Line Item
    """
    line_item: Optional[Dict[str, Any]] = get_item_by_id(
        line_items_collection, line_item_id
    )
    if line_item is None:
        return jsonify({"error": "Line item not found"}), 404
    return jsonify(line_item), 200
