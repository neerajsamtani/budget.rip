"""
Event Hints API endpoints.

Provides CRUD operations for user-configurable event hints,
plus an evaluate endpoint that returns suggestions based on line items.
"""

import logging
from typing import Any

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import get_current_user, jwt_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from models.database import SessionLocal
from models.sql_models import Category, EventHint, LineItem
from utils.cel_evaluator import CELEvaluator, evaluate_hints
from utils.id_generator import generate_id

logger = logging.getLogger(__name__)

event_hints_blueprint = Blueprint("event_hints", __name__)


def _serialize_event_hint(hint: EventHint) -> dict[str, Any]:
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


def _serialize_line_item_for_cel(line_item: LineItem) -> dict[str, Any]:
    """Convert LineItem ORM object to dict for CEL evaluation."""
    return {
        "description": line_item.description or "",
        "amount": float(line_item.amount) if line_item.amount else 0.0,
        "payment_method": line_item.payment_method.name if line_item.payment_method else "",
        "responsible_party": line_item.responsible_party or "",
    }


@event_hints_blueprint.route("/api/event-hints", methods=["GET"])
@jwt_required()
def get_all_event_hints() -> tuple[Response, int]:
    """Get all event hints for the current user, ordered by display_order."""
    user = get_current_user()
    user_id = user["id"]

    db = SessionLocal()
    try:
        hints = (
            db.query(EventHint)
            .options(joinedload(EventHint.prefill_category))
            .filter(EventHint.user_id == user_id)
            .order_by(EventHint.display_order)
            .all()
        )
        logger.info(f"Retrieved {len(hints)} event hints for user {user_id}")
        return jsonify({"data": [_serialize_event_hint(h) for h in hints]}), 200
    finally:
        db.close()


@event_hints_blueprint.route("/api/event-hints/<hint_id>", methods=["GET"])
@jwt_required()
def get_event_hint(hint_id: str) -> tuple[Response, int]:
    """Get a single event hint by ID."""
    user = get_current_user()
    user_id = user["id"]

    db = SessionLocal()
    try:
        hint = (
            db.query(EventHint)
            .options(joinedload(EventHint.prefill_category))
            .filter(EventHint.id == hint_id, EventHint.user_id == user_id)
            .first()
        )
        if not hint:
            return jsonify({"error": "Event hint not found"}), 404
        return jsonify({"data": _serialize_event_hint(hint)}), 200
    finally:
        db.close()


@event_hints_blueprint.route("/api/event-hints", methods=["POST"])
@jwt_required()
def create_event_hint() -> tuple[Response, int]:
    """Create a new event hint."""
    user = get_current_user()
    user_id = user["id"]
    data = request.get_json()

    # Validate required fields
    required_fields = ["name", "cel_expression", "prefill_name"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # Validate CEL expression
    is_valid, error_msg = CELEvaluator.validate(data["cel_expression"])
    if not is_valid:
        return jsonify({"error": f"Invalid CEL expression: {error_msg}"}), 400

    db = SessionLocal()
    try:
        # Get the next display_order for this user
        max_order = db.query(func.max(EventHint.display_order)).filter(EventHint.user_id == user_id).scalar()
        next_order = (max_order or 0) + 1

        # Validate category if provided
        prefill_category_id = data.get("prefill_category_id")
        if prefill_category_id:
            category = db.query(Category).filter(Category.id == prefill_category_id).first()
            if not category:
                return jsonify({"error": f"Category not found: {prefill_category_id}"}), 400

        hint = EventHint(
            id=generate_id("eh"),
            user_id=user_id,
            name=data["name"],
            cel_expression=data["cel_expression"],
            prefill_name=data["prefill_name"],
            prefill_category_id=prefill_category_id,
            display_order=next_order,
            is_active=data.get("is_active", True),
        )
        db.add(hint)
        db.commit()
        db.refresh(hint)

        # Load the category relationship for serialization
        if hint.prefill_category_id:
            hint.prefill_category = db.query(Category).filter(Category.id == hint.prefill_category_id).first()

        logger.info(f"Created event hint {hint.id} for user {user_id}")
        return jsonify({"data": _serialize_event_hint(hint)}), 201
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating event hint: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@event_hints_blueprint.route("/api/event-hints/<hint_id>", methods=["PUT"])
@jwt_required()
def update_event_hint(hint_id: str) -> tuple[Response, int]:
    """Update an existing event hint."""
    user = get_current_user()
    user_id = user["id"]
    data = request.get_json()

    db = SessionLocal()
    try:
        hint = db.query(EventHint).filter(EventHint.id == hint_id, EventHint.user_id == user_id).first()
        if not hint:
            return jsonify({"error": "Event hint not found"}), 404

        # Validate CEL expression if being updated
        if "cel_expression" in data:
            is_valid, error_msg = CELEvaluator.validate(data["cel_expression"])
            if not is_valid:
                return jsonify({"error": f"Invalid CEL expression: {error_msg}"}), 400
            hint.cel_expression = data["cel_expression"]

        # Validate category if being updated
        if "prefill_category_id" in data:
            prefill_category_id = data["prefill_category_id"]
            if prefill_category_id:
                category = db.query(Category).filter(Category.id == prefill_category_id).first()
                if not category:
                    return jsonify({"error": f"Category not found: {prefill_category_id}"}), 400
            hint.prefill_category_id = prefill_category_id

        # Update other fields if provided
        if "name" in data:
            hint.name = data["name"]
        if "prefill_name" in data:
            hint.prefill_name = data["prefill_name"]
        if "is_active" in data:
            hint.is_active = data["is_active"]

        db.commit()
        db.refresh(hint)

        # Load the category relationship for serialization
        if hint.prefill_category_id:
            hint.prefill_category = db.query(Category).filter(Category.id == hint.prefill_category_id).first()

        logger.info(f"Updated event hint {hint_id} for user {user_id}")
        return jsonify({"data": _serialize_event_hint(hint)}), 200
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating event hint: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@event_hints_blueprint.route("/api/event-hints/<hint_id>", methods=["DELETE"])
@jwt_required()
def delete_event_hint(hint_id: str) -> tuple[Response, int]:
    """Delete an event hint."""
    user = get_current_user()
    user_id = user["id"]

    db = SessionLocal()
    try:
        hint = db.query(EventHint).filter(EventHint.id == hint_id, EventHint.user_id == user_id).first()
        if not hint:
            return jsonify({"error": "Event hint not found"}), 404

        db.delete(hint)
        db.commit()

        logger.info(f"Deleted event hint {hint_id} for user {user_id}")
        return jsonify({"message": "Event hint deleted"}), 200
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting event hint: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@event_hints_blueprint.route("/api/event-hints/reorder", methods=["PUT"])
@jwt_required()
def reorder_event_hints() -> tuple[Response, int]:
    """
    Reorder event hints.

    Expects: {"hint_ids": ["eh_xxx", "eh_yyy", "eh_zzz"]}
    Updates display_order to match the provided order.
    """
    user = get_current_user()
    user_id = user["id"]
    data = request.get_json()

    hint_ids = data.get("hint_ids", [])
    if not hint_ids:
        return jsonify({"error": "hint_ids array is required"}), 400

    db = SessionLocal()
    try:
        # Verify all hints belong to this user
        hints = db.query(EventHint).filter(EventHint.id.in_(hint_ids), EventHint.user_id == user_id).all()
        if len(hints) != len(hint_ids):
            return jsonify({"error": "One or more hints not found"}), 404

        # Update display_order based on position in the array
        hint_map = {h.id: h for h in hints}
        for order, hint_id in enumerate(hint_ids):
            if hint_id in hint_map:
                hint_map[hint_id].display_order = order

        db.commit()

        logger.info(f"Reordered {len(hint_ids)} event hints for user {user_id}")
        return jsonify({"message": "Hints reordered"}), 200
    except Exception as e:
        db.rollback()
        logger.error(f"Error reordering event hints: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@event_hints_blueprint.route("/api/event-hints/evaluate", methods=["POST"])
@jwt_required()
def evaluate_event_hints() -> tuple[Response, int]:
    """
    Evaluate hints against provided line items.

    Expects: {"line_item_ids": ["li_xxx", "li_yyy"]}
    Returns: {"data": {"suggestion": {...}}} or {"data": {"suggestion": null}}
    """
    user = get_current_user()
    user_id = user["id"]
    data = request.get_json()

    line_item_ids = data.get("line_item_ids", [])
    if not line_item_ids:
        return jsonify({"data": {"suggestion": None}}), 200

    db = SessionLocal()
    try:
        # Get line items
        line_items = (
            db.query(LineItem).options(joinedload(LineItem.payment_method)).filter(LineItem.id.in_(line_item_ids)).all()
        )

        if not line_items:
            return jsonify({"data": {"suggestion": None}}), 200

        # Get user's active hints in order
        hints = (
            db.query(EventHint)
            .options(joinedload(EventHint.prefill_category))
            .filter(EventHint.user_id == user_id, EventHint.is_active == True)  # noqa: E712
            .order_by(EventHint.display_order)
            .all()
        )

        if not hints:
            return jsonify({"data": {"suggestion": None}}), 200

        # Convert to dicts for CEL evaluation
        line_item_dicts = [_serialize_line_item_for_cel(li) for li in line_items]
        hint_dicts = [_serialize_event_hint(h) for h in hints]

        # Evaluate hints
        suggestion = evaluate_hints(hint_dicts, line_item_dicts)

        logger.debug(f"Evaluated {len(hints)} hints against {len(line_items)} line items for user {user_id}")
        return jsonify({"data": {"suggestion": suggestion}}), 200
    finally:
        db.close()


@event_hints_blueprint.route("/api/event-hints/validate", methods=["POST"])
@jwt_required()
def validate_cel_expression() -> tuple[Response, int]:
    """
    Validate a CEL expression without saving.

    Expects: {"cel_expression": "description contains \"Spotify\""}
    Returns: {"data": {"is_valid": true}} or {"data": {"is_valid": false, "error": "..."}}
    """
    data = request.get_json()
    cel_expression = data.get("cel_expression", "")

    is_valid, error_msg = CELEvaluator.validate(cel_expression)

    if is_valid:
        return jsonify({"data": {"is_valid": True}}), 200
    else:
        return jsonify({"data": {"is_valid": False, "error": error_msg}}), 200
