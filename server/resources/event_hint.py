"""
Event Hints API endpoints.

Provides CRUD operations for user-configurable event hints,
plus an evaluate endpoint that returns suggestions based on line items.
"""

import logging
from typing import Any

from apiflask import APIBlueprint, abort
from flask_jwt_extended import get_current_user, jwt_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from helpers import get_or_404
from models.database import SessionLocal
from models.sql_models import Category, EventHint, LineItem
from resources._common import JWT_SECURITY, STANDARD_ERROR_RESPONSES
from resources.schemas.event_hint import (
    EvaluateIn,
    EvaluateResponse,
    EventHintCreateIn,
    EventHintListResponse,
    EventHintSingleResponse,
    EventHintUpdateIn,
    MessageResponse,
    ReorderIn,
    ValidateCelIn,
    ValidateCelResponse,
)
from utils.cel_evaluator import CELEvaluator, evaluate_hints
from utils.id_generator import generate_id

logger = logging.getLogger(__name__)

event_hints_blueprint = APIBlueprint("event_hints", __name__)


def serialize_event_hint(hint: EventHint) -> dict[str, Any]:
    """Convert EventHint ORM object to dict."""
    return {
        "id": hint.id,
        "name": hint.name,
        "cel_expression": hint.cel_expression,
        "prefill_name": hint.prefill_name,
        "prefill_category": hint.prefill_category.name if hint.prefill_category else None,
        "prefill_category_id": hint.prefill_category_id,
        "display_order": hint.display_order,
        "is_active": hint.is_active,
    }


def serialize_line_item_for_cel(line_item: LineItem) -> dict[str, Any]:
    """Convert LineItem ORM object to dict for CEL evaluation."""
    return {
        "description": line_item.description or "",
        "amount": float(line_item.amount) if line_item.amount else 0.0,
        "payment_method": line_item.payment_method.name if line_item.payment_method else "",
        "responsible_party": line_item.responsible_party or "",
    }


@event_hints_blueprint.get("/api/event-hints")
@event_hints_blueprint.output(EventHintListResponse)
@event_hints_blueprint.doc(security=JWT_SECURITY)
@jwt_required()
def get_all_event_hints():
    """Get all event hints for the current user, ordered by display_order."""
    user_id = get_current_user()["id"]

    with SessionLocal.begin() as db:
        hints = (
            db.query(EventHint)
            .options(joinedload(EventHint.prefill_category))
            .filter(EventHint.user_id == user_id)
            .order_by(EventHint.display_order)
            .all()
        )
        return EventHintListResponse(data=[serialize_event_hint(h) for h in hints])


@event_hints_blueprint.get("/api/event-hints/<hint_id>")
@event_hints_blueprint.output(EventHintSingleResponse)
@event_hints_blueprint.doc(security=JWT_SECURITY, responses=STANDARD_ERROR_RESPONSES)
@jwt_required()
def get_event_hint(hint_id: str):
    """Get a single event hint by ID."""
    user_id = get_current_user()["id"]

    with SessionLocal.begin() as db:
        hint = get_or_404(
            db.query(EventHint)
            .options(joinedload(EventHint.prefill_category))
            .filter(EventHint.id == hint_id, EventHint.user_id == user_id)
            .first(),
            "Event hint not found",
        )
        return EventHintSingleResponse(data=serialize_event_hint(hint))


@event_hints_blueprint.post("/api/event-hints")
@event_hints_blueprint.input(EventHintCreateIn, arg_name="body")
@event_hints_blueprint.output(EventHintSingleResponse, status_code=201)
@event_hints_blueprint.doc(security=JWT_SECURITY, responses=STANDARD_ERROR_RESPONSES)
@jwt_required()
def create_event_hint(body: EventHintCreateIn):
    """Create a new event hint."""
    user_id = get_current_user()["id"]

    missing = [f for f in ["name", "cel_expression", "prefill_name"] if not getattr(body, f, None)]
    if missing:
        abort(400, message=f"Missing required fields: {', '.join(missing)}")

    is_valid, error_msg = CELEvaluator.validate(body.cel_expression)
    if not is_valid:
        abort(400, message=f"Invalid CEL expression: {error_msg}")

    with SessionLocal.begin() as db:
        max_order = db.query(func.max(EventHint.display_order)).filter(EventHint.user_id == user_id).scalar()
        next_order = (max_order or 0) + 1

        if body.prefill_category_id:
            if not db.query(Category).filter(Category.id == body.prefill_category_id).first():
                abort(400, message=f"Category not found: {body.prefill_category_id}")

        hint = EventHint(
            id=generate_id("eh"),
            user_id=user_id,
            name=body.name,
            cel_expression=body.cel_expression,
            prefill_name=body.prefill_name,
            prefill_category_id=body.prefill_category_id,
            display_order=next_order,
            is_active=body.is_active if body.is_active is not None else True,
        )
        db.add(hint)

        db.flush()
        hint = db.query(EventHint).options(joinedload(EventHint.prefill_category)).filter(EventHint.id == hint.id).first()

        return EventHintSingleResponse(data=serialize_event_hint(hint)), 201


@event_hints_blueprint.put("/api/event-hints/reorder")
@event_hints_blueprint.input(ReorderIn, arg_name="body")
@event_hints_blueprint.output(MessageResponse)
@event_hints_blueprint.doc(security=JWT_SECURITY, responses=STANDARD_ERROR_RESPONSES)
@jwt_required()
def reorder_event_hints(body: ReorderIn):
    """
    Reorder event hints.

    Updates display_order to match the provided order.
    """
    user_id = get_current_user()["id"]

    if not body.hint_ids:
        abort(400, message="hint_ids array is required")

    with SessionLocal.begin() as db:
        hints = db.query(EventHint).filter(EventHint.id.in_(body.hint_ids), EventHint.user_id == user_id).all()
        if len(hints) != len(body.hint_ids):
            abort(404, message="One or more hints not found")

        hint_map = {h.id: h for h in hints}
        for order, hint_id in enumerate(body.hint_ids):
            if hint_id in hint_map:
                hint_map[hint_id].display_order = order

        return MessageResponse(message="Hints reordered")


@event_hints_blueprint.post("/api/event-hints/evaluate")
@event_hints_blueprint.input(EvaluateIn, arg_name="body")
@event_hints_blueprint.output(EvaluateResponse)
@event_hints_blueprint.doc(security=JWT_SECURITY)
@jwt_required()
def evaluate_event_hints(body: EvaluateIn):
    """
    Evaluate hints against provided line items.

    Returns a suggestion dict or null.
    """
    user_id = get_current_user()["id"]

    if not body.line_item_ids:
        return EvaluateResponse(data={"suggestion": None})

    with SessionLocal.begin() as db:
        line_items = (
            db.query(LineItem).options(joinedload(LineItem.payment_method)).filter(LineItem.id.in_(body.line_item_ids)).all()
        )

        if not line_items:
            return EvaluateResponse(data={"suggestion": None})

        hints = (
            db.query(EventHint)
            .options(joinedload(EventHint.prefill_category))
            .filter(EventHint.user_id == user_id, EventHint.is_active.is_(True))
            .order_by(EventHint.display_order)
            .all()
        )

        if not hints:
            return EvaluateResponse(data={"suggestion": None})

        line_item_dicts = [serialize_line_item_for_cel(li) for li in line_items]
        hint_dicts = [serialize_event_hint(h) for h in hints]

        suggestion = evaluate_hints(hint_dicts, line_item_dicts)

        return EvaluateResponse(data={"suggestion": suggestion})


@event_hints_blueprint.post("/api/event-hints/validate")
@event_hints_blueprint.input(ValidateCelIn, arg_name="body")
@event_hints_blueprint.output(ValidateCelResponse)
@event_hints_blueprint.doc(security=JWT_SECURITY)
@jwt_required()
def validate_cel_expression(body: ValidateCelIn):
    """Validate a CEL expression without saving."""
    is_valid, error_msg = CELEvaluator.validate(body.cel_expression)

    if is_valid:
        return ValidateCelResponse(data={"is_valid": True})
    return ValidateCelResponse(data={"is_valid": False, "error": error_msg})


@event_hints_blueprint.put("/api/event-hints/<hint_id>")
@event_hints_blueprint.input(EventHintUpdateIn, arg_name="body")
@event_hints_blueprint.output(EventHintSingleResponse)
@event_hints_blueprint.doc(security=JWT_SECURITY, responses=STANDARD_ERROR_RESPONSES)
@jwt_required()
def update_event_hint(hint_id: str, body: EventHintUpdateIn):
    """Update an existing event hint."""
    user_id = get_current_user()["id"]

    with SessionLocal.begin() as db:
        hint = get_or_404(
            db.query(EventHint).filter(EventHint.id == hint_id, EventHint.user_id == user_id).first(),
            "Event hint not found",
        )

        if body.cel_expression is not None:
            is_valid, error_msg = CELEvaluator.validate(body.cel_expression)
            if not is_valid:
                abort(400, message=f"Invalid CEL expression: {error_msg}")
            hint.cel_expression = body.cel_expression

        if body.prefill_category_id is not None:
            if body.prefill_category_id:
                if not db.query(Category).filter(Category.id == body.prefill_category_id).first():
                    abort(400, message=f"Category not found: {body.prefill_category_id}")
            hint.prefill_category_id = body.prefill_category_id

        if body.name is not None:
            hint.name = body.name
        if body.prefill_name is not None:
            hint.prefill_name = body.prefill_name
        if body.is_active is not None:
            hint.is_active = body.is_active

        db.flush()
        hint = db.query(EventHint).options(joinedload(EventHint.prefill_category)).filter(EventHint.id == hint_id).first()

        return EventHintSingleResponse(data=serialize_event_hint(hint))


@event_hints_blueprint.delete("/api/event-hints/<hint_id>")
@event_hints_blueprint.output(MessageResponse, status_code=204)
@event_hints_blueprint.doc(security=JWT_SECURITY, responses=STANDARD_ERROR_RESPONSES)
@jwt_required()
def delete_event_hint(hint_id: str):
    """Delete an event hint."""
    user_id = get_current_user()["id"]

    with SessionLocal.begin() as db:
        hint = get_or_404(
            db.query(EventHint).filter(EventHint.id == hint_id, EventHint.user_id == user_id).first(),
            "Event hint not found",
        )
        db.delete(hint)

    return MessageResponse(message="Event hint deleted"), 204
