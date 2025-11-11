import logging
from typing import Any, Dict, List, Optional

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import get_current_user, jwt_required

from constants import LARGEST_EPOCH_TIME, SMALLEST_EPOCH_TIME
from dao import (
    bulk_upsert,
    delete_from_collection,
    events_collection,
    get_all_data,
    get_item_by_id,
    line_items_collection,
    remove_event_from_line_item,
    upsert_with_id,
)
from helpers import html_date_to_posix
from models.sql_models import Event
from utils.dual_write import dual_write_operation

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
    logging.info(f"Current User: {get_current_user()['email']}")
    start_time: float = float(request.args.get("start_time", SMALLEST_EPOCH_TIME))
    end_time: float = float(request.args.get("end_time", LARGEST_EPOCH_TIME))
    filters["date"] = {"$gte": start_time, "$lte": end_time}
    events: List[Dict[str, Any]] = get_all_data(events_collection, filters)
    events_total: float = sum(event["amount"] for event in events)
    logging.info(f"Retrieved {len(events)} events (total: ${events_total:.2f})")
    return jsonify({"total": events_total, "data": events}), 200


@events_blueprint.route("/api/events/<event_id>", methods=["GET"])
@jwt_required()
def get_event_api(event_id: str) -> tuple[Response, int]:
    """
    Get An Event
    """
    event: Optional[Dict[str, Any]] = get_item_by_id(events_collection, event_id)
    if event is None:
        logging.warning(f"Event not found: {event_id}")
        return jsonify({"error": "Event not found"}), 404
    logging.info(f"Retrieved event: {event_id}")
    return jsonify(event), 200


@events_blueprint.route("/api/events", methods=["POST"])
@jwt_required()
def post_event_api() -> tuple[Response, int]:
    """
    Create An Event (with dual-write to PostgreSQL)
    """
    new_event: Dict[str, Any] = request.get_json()
    if len(new_event["line_items"]) == 0:
        logging.warning("Event creation attempt with no line items")
        return jsonify("Failed to Create Event: No Line Items Submitted"), 400

    filters: Dict[str, Any] = {}
    filters["_id"] = {"$in": new_event["line_items"]}
    line_items: List[Dict[str, Any]] = get_all_data(line_items_collection, filters)
    earliest_line_item: Dict[str, Any] = min(line_items, key=lambda line_item: line_item["date"])

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

    # MongoDB write function
    def mongo_write():
        upsert_with_id(events_collection, new_event, new_event["id"])
        # Update all line items with event_id and bulk upsert
        for line_item in line_items:
            line_item["event_id"] = new_event["id"]
        bulk_upsert(line_items_collection, line_items)

    # PostgreSQL write function
    def pg_write(db_session):
        from utils.pg_event_operations import upsert_event_to_postgresql

        # Use extracted helper function
        # This will raise ValueError if category missing/not found
        # The dual_write_operation will catch and handle appropriately
        upsert_event_to_postgresql(new_event, db_session)
        # Note: No explicit commit needed - dual_write_operation handles it

    # Execute dual-write
    dual_write_operation(
        operation_name="create_event",
        mongo_write_func=mongo_write,
        pg_write_func=pg_write,
    )

    logging.info(f"Created event: {new_event['id']} with {len(line_items)} line items (amount: ${new_event['amount']:.2f})")
    return jsonify(new_event), 201


@events_blueprint.route("/api/events/<event_id>", methods=["DELETE"])
@jwt_required()
def delete_event_api(event_id: str) -> tuple[Response, int]:
    """
    Delete An Event (with dual-write to PostgreSQL and ID coexistence)
    """
    # Use ID coexistence to get event from either database
    event: Optional[Dict[str, Any]] = get_item_by_id(events_collection, event_id)
    if event is None:
        logging.warning(f"Event deletion attempt for non-existent event: {event_id}")
        return jsonify({"error": "Event not found"}), 404

    line_item_ids: List[str] = event["line_items"]

    # MongoDB write function
    def mongo_write():
        delete_from_collection(events_collection, event_id)
        for line_item_id in line_item_ids:
            remove_event_from_line_item(line_item_id)

    # PostgreSQL write function
    def pg_write(db_session):
        # Find event by exact ID first, then by mongo_id
        # Unique constraint on mongo_id ensures at most one event per ID
        pg_event = db_session.query(Event).filter(Event.id == event_id).first()
        if not pg_event:
            pg_event = db_session.query(Event).filter(Event.mongo_id == event_id).first()

        if pg_event:
            db_session.delete(pg_event)
        else:
            logging.info(f"Event {event_id} not in PostgreSQL yet")

    # Execute dual-write
    dual_write_operation(
        operation_name="delete_event",
        mongo_write_func=mongo_write,
        pg_write_func=pg_write,
    )

    logging.info(f"Deleted event: {event_id} with {len(line_item_ids)} line items")
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
            logging.warning(f"Line items request for non-existent event: {event_id}")
            return jsonify({"error": "Event not found"}), 404
        line_items: List[Dict[str, Any]] = []
        for line_item_id in event["line_items"]:
            line_item: Optional[Dict[str, Any]] = get_item_by_id(line_items_collection, line_item_id)
            if line_item is not None:
                line_items.append(line_item)
        logging.info(f"Retrieved {len(line_items)} line items for event: {event_id}")
        return jsonify({"data": line_items}), 200
    except Exception as e:
        logging.error(f"Error retrieving line items for event {event_id}: {e}")
        return jsonify(error=str(e)), 500
