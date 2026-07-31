"""Review endpoints for materialized single-line-item event suggestions."""

from datetime import UTC, datetime
from typing import Any

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import get_current_user, jwt_required

from models.database import SessionLocal
from models.sql_models import EventLineItem, EventSuggestion
from serializers import serialize_datetime
from utils.pg_event_operations import upsert_event_to_postgresql

event_suggestions_blueprint = Blueprint("event_suggestions", __name__)


@event_suggestions_blueprint.route("/api/event-suggestions/<suggestion_id>/accept", methods=["POST"])
@jwt_required()
def accept_event_suggestion(suggestion_id: str) -> tuple[Response, int]:
    """Create the suggested event, optionally overriding its title."""
    user_id = get_current_user()["id"]
    data: dict[str, Any] = request.get_json(silent=True) or {}

    with SessionLocal.begin() as db:
        suggestion = (
            db.query(EventSuggestion)
            .filter(
                EventSuggestion.id == suggestion_id,
                EventSuggestion.user_id == user_id,
                EventSuggestion.rejected_at.is_(None),
            )
            .with_for_update()
            .first()
        )
        if not suggestion:
            return jsonify({"error": "Event suggestion not found"}), 404

        name = str(data.get("name", suggestion.suggested_name)).strip()
        if not name:
            return jsonify({"error": "Event name is required"}), 400
        if not suggestion.category:
            return jsonify({"error": "Suggested category is no longer available"}), 409

        already_reviewed = db.query(EventLineItem.id).filter(EventLineItem.line_item_id == suggestion.line_item_id).first()
        if already_reviewed:
            db.delete(suggestion)
            return jsonify({"error": "Line item has already been added to an event"}), 409

        line_item = suggestion.line_item
        event_dict = {
            "name": name,
            "category": suggestion.category.name,
            "date": serialize_datetime(line_item.date),
            "line_items": [line_item.id],
            "is_duplicate_transaction": False,
            "tags": [],
        }
        event_id = upsert_event_to_postgresql(event_dict, db, user_id)

        return (
            jsonify(
                {
                    "id": event_id,
                    **event_dict,
                    "amount": float(line_item.amount),
                }
            ),
            201,
        )


@event_suggestions_blueprint.route("/api/event-suggestions/<suggestion_id>/reject", methods=["POST"])
@jwt_required()
def reject_event_suggestion(suggestion_id: str) -> tuple[Response, int]:
    """Permanently suppress a suggestion for this user and line item."""
    user_id = get_current_user()["id"]

    with SessionLocal.begin() as db:
        suggestion = (
            db.query(EventSuggestion).filter(EventSuggestion.id == suggestion_id, EventSuggestion.user_id == user_id).first()
        )
        if not suggestion:
            return jsonify({"error": "Event suggestion not found"}), 404
        suggestion.rejected_at = datetime.now(UTC)

    return Response(status=204), 204
