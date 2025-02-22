from constants import LARGEST_EPOCH_TIME, SMALLEST_EPOCH_TIME
from dao import (
    delete_from_collection,
    events_collection,
    get_all_data,
    get_item_by_id,
    line_items_collection,
    remove_event_from_line_item,
    upsert,
    upsert_with_id,
)
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_current_user
from helpers import html_date_to_posix

events_blueprint = Blueprint("events", __name__)

# TODO: Exceptions


@events_blueprint.route("/api/events", methods=["GET"])
@jwt_required()
def all_events_api():
    """
    Get All Events
    Filters:
        - Start Time
        - End Time
    """
    filters = {}
    print(f"Current User: {get_current_user()['email']}")
    start_time = float(request.args.get("start_time", SMALLEST_EPOCH_TIME))
    end_time = float(request.args.get("end_time", LARGEST_EPOCH_TIME))
    filters["date"] = {"$gte": start_time, "$lte": end_time}
    events = get_all_data(events_collection, filters)
    events_total = sum(event["amount"] for event in events)
    return jsonify({"total": events_total, "data": events})


@events_blueprint.route("/api/events/<event_id>", methods=["GET"])
@jwt_required()
def get_event_api(event_id):
    """
    Get An Event
    """
    event = get_item_by_id(events_collection, event_id)
    return jsonify(event)


@events_blueprint.route("/api/events", methods=["POST"])
@jwt_required()
def post_event_api():
    """
    Create An Event
    """
    new_event = request.get_json()
    if len(new_event["line_items"]) == 0:
        return jsonify("Failed to Create Event: No Line Items Submitted")

    filters = {}
    filters["_id"] = {"$in": new_event["line_items"]}
    line_items = get_all_data(line_items_collection, filters)
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

    # Ensure tags is always a list
    new_event["tags"] = new_event.get("tags", [])

    upsert_with_id(events_collection, new_event, new_event["id"])
    for line_item in line_items:
        line_item["event_id"] = new_event["id"]
        upsert(line_items_collection, line_item)

    return jsonify("Created Event")


@events_blueprint.route("/api/events/<event_id>", methods=["DELETE"])
@jwt_required()
def delete_event_api(event_id):
    """
    Delete An Event
    """
    event = get_item_by_id(events_collection, event_id)
    line_item_ids = event["line_items"]
    delete_from_collection(events_collection, event_id)
    for line_item_id in line_item_ids:
        remove_event_from_line_item(line_item_id)
    return jsonify("Deleted Event")


@events_blueprint.route("/api/events/<event_id>/line_items_for_event", methods=["GET"])
@jwt_required()
def get_line_items_for_event_api(event_id):
    """
    Get All Line Items Belonging To An Event
    """
    try:
        event = get_item_by_id(events_collection, event_id)
        line_items = []
        for line_item_id in event["line_items"]:
            line_items.append(get_item_by_id(line_items_collection, line_item_id))
        return jsonify({"data": line_items})
    except Exception as e:
        return jsonify(error=str(e)), 403
