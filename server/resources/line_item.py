from dao import get_all_data, get_item_by_id, line_items_collection
from flask import Blueprint, jsonify, request
from helpers import sort_by_date

line_items = Blueprint("line_items", __name__)

# TODO: Exceptions


@line_items.route("/api/line_items", methods=["GET"])
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


@line_items.route("/api/line_items/<line_item_id>", methods=["GET"])
def get_line_item(line_item_id):
    """
    Get A Line Item
    """
    line_item = get_item_by_id(line_items_collection, line_item_id)
    return jsonify(line_item)
