import logging
from typing import Any, Dict, List, Optional

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import get_current_user, jwt_required

from constants import LARGEST_EPOCH_TIME, SMALLEST_EPOCH_TIME
from dao import (
    events_collection,
    get_all_data,
    get_item_by_id,
    line_items_collection,
)
from helpers import html_date_to_posix

logger = logging.getLogger(__name__)

events_blueprint = Blueprint("events", __name__)

# TODO: Exceptions


@events_blueprint.route("/api/events", methods=["GET"])
@jwt_required()
def all_events_api() -> tuple[Response, int]:
    """
    Get All Events
    Filters:
        - Start Time
        - End Time
    """
    filters: Dict[str, Any] = {}
    logger.info(f"Current User: {get_current_user()['email']}")
    start_time: float = float(request.args.get("start_time", SMALLEST_EPOCH_TIME))
    end_time: float = float(request.args.get("end_time", LARGEST_EPOCH_TIME))
    filters["date"] = {"$gte": start_time, "$lte": end_time}
    events: List[Dict[str, Any]] = get_all_data(events_collection, filters)
    events_total: float = sum(event["amount"] for event in events)
    logger.info(f"Retrieved {len(events)} events (total: ${events_total:.2f})")
    return jsonify({"total": events_total, "data": events}), 200


@events_blueprint.route("/api/events/<event_id>", methods=["GET"])
@jwt_required()
def get_event_api(event_id: str) -> tuple[Response, int]:
    """
    Get An Event
    """
    event: Optional[Dict[str, Any]] = get_item_by_id(events_collection, event_id)
    if event is None:
        logger.warning(f"Event not found: {event_id}")
        return jsonify({"error": "Event not found"}), 404
    logger.info(f"Retrieved event: {event_id}")
    return jsonify(event), 200


@events_blueprint.route("/api/events", methods=["POST"])
@jwt_required()
def post_event_api() -> tuple[Response, int]:
    """
    Create An Event
    """
    new_event: Dict[str, Any] = request.get_json()

    # Validate required fields
    if "line_items" not in new_event:
        logger.warning("Event creation attempt without line_items field")
        return jsonify({"error": "Missing required field: line_items"}), 400

    if len(new_event["line_items"]) == 0:
        logger.warning("Event creation attempt with no line items")
        return jsonify("Failed to Create Event: No Line Items Submitted"), 400

    filters: Dict[str, Any] = {}
    filters["_id"] = {"$in": new_event["line_items"]}
    line_items: List[Dict[str, Any]] = get_all_data(line_items_collection, filters)
    earliest_line_item: Dict[str, Any] = min(line_items, key=lambda line_item: line_item["date"])

    if new_event.get("date"):
        new_event["date"] = html_date_to_posix(new_event["date"])
    else:
        new_event["date"] = earliest_line_item["date"]

    if new_event.get("is_duplicate_transaction"):
        new_event["amount"] = line_items[0]["amount"]
    else:
        new_event["amount"] = sum(line_item["amount"] for line_item in line_items)

    # Ensure tags is always a list
    new_event["tags"] = new_event.get("tags", [])

    from utils.pg_event_operations import upsert_event

    pg_event_id = upsert_event(new_event)
    new_event["id"] = pg_event_id

    logger.info(f"Created event: {new_event['id']} with {len(line_items)} line items (amount: ${new_event['amount']:.2f})")
    return jsonify(new_event), 201


@events_blueprint.route("/api/events/<event_id>", methods=["DELETE"])
@jwt_required()
def delete_event_api(event_id: str) -> tuple[Response, int]:
    """
    Delete An Event
    """
    # Check if event exists
    event: Optional[Dict[str, Any]] = get_item_by_id(events_collection, event_id)
    if event is None:
        logger.warning(f"Event deletion attempt for non-existent event: {event_id}")
        return jsonify({"error": "Event not found"}), 404

    line_item_ids: List[str] = event["line_items"]

    from utils.pg_event_operations import delete_event_from_postgresql

    deleted = delete_event_from_postgresql(event_id)
    if not deleted:
        logger.warning(f"Event {event_id} not found in database")
        return jsonify({"error": "Event not found"}), 404

    logger.info(f"Deleted event: {event_id} with {len(line_item_ids)} line items")
    return jsonify("Deleted Event"), 200


@events_blueprint.route("/api/events/<event_id>/line_items_for_event", methods=["GET"])
@jwt_required()
def get_line_items_for_event_api(
    event_id: str,
) -> tuple[Response, int]:
    """
    Get All Line Items Belonging To An Event
    """
    try:
        event: Optional[Dict[str, Any]] = get_item_by_id(events_collection, event_id)
        if event is None:
            logger.warning(f"Line items request for non-existent event: {event_id}")
            return jsonify({"error": "Event not found"}), 404
        line_items: List[Dict[str, Any]] = []
        for line_item_id in event["line_items"]:
            line_item: Optional[Dict[str, Any]] = get_item_by_id(line_items_collection, line_item_id)
            if line_item is not None:
                line_items.append(line_item)
        logger.info(f"Retrieved {len(line_items)} line items for event: {event_id}")
        return jsonify({"data": line_items}), 200
    except Exception as e:
        logger.error(f"Error retrieving line items for event {event_id}: {e}")
        return jsonify(error=str(e)), 500
