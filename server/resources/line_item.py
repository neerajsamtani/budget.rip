import json

from dao import get_all_data, get_item_by_id, line_items_collection
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from helpers import sort_by_date

line_items_blueprint = Blueprint("line_items", __name__)

# TODO: Exceptions


class LineItem:
    def __init__(
        self, id, date, responsible_party, payment_method, description, amount
    ):
        self.id = id
        self.date = date
        self.responsible_party = responsible_party
        self.payment_method = payment_method
        self.description = description
        self.amount = amount

    def serialize(self):
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

    def to_json(self):
        """
        convert the instance of this class to json
        """
        return json.dumps(self, indent=4, default=lambda o: o.__dict__)


@line_items_blueprint.route("/api/line_items", methods=["GET"])
@jwt_required()
def all_line_items(local_only_line_items_to_review=False):
    """
    Get All Line Items
    Filters:
        - Payment Method (optional)
        - Only Line Items To Review (optional)
    """
    filters = {}
    payment_method = request.args.get("payment_method")
    if payment_method not in ["All", None]:
        filters["payment_method"] = payment_method

    only_line_items_to_review = request.args.get("only_line_items_to_review")
    if only_line_items_to_review or local_only_line_items_to_review:
        filters["event_id"] = {"$exists": False}

    line_items = get_all_data(line_items_collection, filters)
    line_items = sort_by_date(line_items)
    line_items_total = sum(line_item["amount"] for line_item in line_items)
    return jsonify({"total": line_items_total, "data": line_items})


@line_items_blueprint.route("/api/line_items/<line_item_id>", methods=["GET"])
def get_line_item(line_item_id):
    """
    Get A Line Item
    """
    line_item = get_item_by_id(line_items_collection, line_item_id)
    return jsonify(line_item)
