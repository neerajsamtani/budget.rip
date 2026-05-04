import logging

from apiflask import APIBlueprint, abort
from flask import request
from flask_jwt_extended import get_current_user, jwt_required

from constants import LARGEST_EPOCH_TIME, SMALLEST_EPOCH_TIME
from dao import (
    get_all_events,
    get_all_line_items,
    get_event_by_id,
    get_line_item_amounts,
)
from helpers import get_or_404, html_date_to_posix
from resources.schemas.event import (
    ErrorResponse,
    EventCreateIn,
    EventLineItemsResponse,
    EventListResponse,
    EventOut,
    EventUpdateIn,
    MessageResponse,
)

logger = logging.getLogger(__name__)

events_blueprint = APIBlueprint("events", __name__)

_SECURITY = [{"jwtCookie": []}]
_ERROR_RESPONSES = {
    400: {"description": "Bad request", "schema": ErrorResponse},
    404: {"description": "Not found", "schema": ErrorResponse},
}


@events_blueprint.get("/api/events")
@events_blueprint.output(EventListResponse)
@events_blueprint.doc(security=_SECURITY)
@jwt_required()
def all_events_api():
    """Get all events, optionally filtered by date range."""
    logger.info(f"Current User: {get_current_user()['email']}")
    start_time: float = float(request.args.get("start_time", SMALLEST_EPOCH_TIME))
    end_time: float = float(request.args.get("end_time", LARGEST_EPOCH_TIME))
    filters = {"date": {"$gte": start_time, "$lte": end_time}}
    events = get_all_events(filters)
    events_total: float = sum(event["amount"] for event in events)
    logger.info(f"Retrieved {len(events)} events (total: ${events_total:.2f})")
    return EventListResponse(total=events_total, data=events)


@events_blueprint.get("/api/events/<event_id>")
@events_blueprint.output(EventOut)
@events_blueprint.doc(security=_SECURITY, responses=_ERROR_RESPONSES)
@jwt_required()
def get_event_api(event_id: str):
    """Get a single event by ID."""
    event = get_or_404(get_event_by_id(event_id), "Event not found")
    logger.info(f"Retrieved event: {event_id}")
    return EventOut(**event)


@events_blueprint.post("/api/events")
@events_blueprint.input(EventCreateIn, arg_name="body")
@events_blueprint.output(EventOut, status_code=201)
@events_blueprint.doc(security=_SECURITY, responses=_ERROR_RESPONSES)
@jwt_required()
def post_event_api(body: EventCreateIn):
    """Create a new event from one or more line items."""
    if len(body.line_items) == 0:
        logger.warning("Event creation attempt with no line items")
        abort(400, message="Failed to Create Event: No Line Items Submitted")

    line_items = get_line_item_amounts(body.line_items)
    earliest_line_item = min(line_items, key=lambda li: li["date"])

    date = html_date_to_posix(body.date) if body.date else earliest_line_item["date"]
    amount = line_items[0]["amount"] if body.is_duplicate_transaction else sum(li["amount"] for li in line_items)

    event_dict = {
        "name": body.name,
        "category": body.category,
        "date": date,
        "line_items": body.line_items,
        "tags": body.tags,
        "is_duplicate_transaction": body.is_duplicate_transaction,
        "amount": amount,
    }

    from utils.pg_event_operations import upsert_event

    pg_event_id = upsert_event(event_dict)
    logger.info(f"Created event: {pg_event_id} with {len(line_items)} line items (amount: ${amount:.2f})")
    return EventOut(
        id=pg_event_id,
        name=body.name,
        category=body.category,
        date=date,
        amount=amount,
        line_items=body.line_items,
        tags=body.tags,
        is_duplicate_transaction=body.is_duplicate_transaction,
    ), 201


@events_blueprint.put("/api/events/<event_id>")
@events_blueprint.input(EventUpdateIn, arg_name="body")
@events_blueprint.output(EventOut)
@events_blueprint.doc(security=_SECURITY, responses=_ERROR_RESPONSES)
@jwt_required()
def update_event_api(event_id: str, body: EventUpdateIn):
    """Update an existing event."""
    event = get_or_404(get_event_by_id(event_id), "Event not found")

    if len(body.line_items) == 0:
        logger.warning("Event update attempt with no line items")
        abort(400, message="Event must have at least one line item")

    filters = {"id": {"$in": body.line_items}}
    line_items = get_all_line_items(filters)
    earliest_line_item = min(line_items, key=lambda li: li["date"])

    date = html_date_to_posix(body.date) if body.date else earliest_line_item["date"]
    amount = line_items[0]["amount"] if body.is_duplicate_transaction else sum(li["amount"] for li in line_items)

    event_dict = {
        "id": event_id,
        "name": body.name if body.name is not None else event.get("name", ""),
        "category": body.category if body.category is not None else event.get("category"),
        "line_items": body.line_items,
        "is_duplicate_transaction": body.is_duplicate_transaction,
        "tags": body.tags,
        "date": date,
    }

    from utils.pg_event_operations import upsert_event

    upsert_event(event_dict)
    logger.info(f"Updated event: {event_id} with {len(line_items)} line items")
    return EventOut(
        id=event_id,
        name=event_dict["name"],
        category=event_dict["category"],
        date=date,
        amount=amount,
        line_items=body.line_items,
        tags=body.tags,
        is_duplicate_transaction=body.is_duplicate_transaction,
    )


@events_blueprint.delete("/api/events/<event_id>")
@events_blueprint.output(MessageResponse, status_code=204)
@events_blueprint.doc(security=_SECURITY, responses=_ERROR_RESPONSES)
@jwt_required()
def delete_event_api(event_id: str):
    """Delete an event and unlink its line items."""
    get_or_404(get_event_by_id(event_id), "Event not found")

    from utils.pg_event_operations import delete_event_from_postgresql

    deleted = delete_event_from_postgresql(event_id)
    if not deleted:
        logger.warning(f"Event {event_id} not found in database")
        abort(404, message="Event not found")

    logger.info(f"Deleted event: {event_id}")
    return MessageResponse(message="Event deleted"), 204


@events_blueprint.get("/api/events/<event_id>/line_items_for_event")
@events_blueprint.output(EventLineItemsResponse)
@events_blueprint.doc(security=_SECURITY, responses=_ERROR_RESPONSES)
@jwt_required()
def get_line_items_for_event_api(event_id: str):
    """Get all line items belonging to an event."""
    event = get_or_404(get_event_by_id(event_id), "Event not found")
    filters = {"id": {"$in": event["line_items"]}}
    line_items = get_all_line_items(filters)
    logger.info(f"Retrieved {len(line_items)} line items for event: {event_id}")
    return EventLineItemsResponse(data=line_items)
