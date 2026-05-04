import logging

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import get_current_user, jwt_required

from dao import get_unread_notifications, mark_notifications_read

logger = logging.getLogger(__name__)

notification_blueprint = Blueprint("notifications", __name__)


@notification_blueprint.route("/api/notifications", methods=["GET"])
@jwt_required()
def get_notifications() -> tuple[Response, int]:
    """Get unread notifications for the current user."""
    user = get_current_user()
    notifications = get_unread_notifications(user["id"])
    return jsonify({"data": notifications}), 200


@notification_blueprint.route("/api/notifications/mark-read", methods=["POST"])
@jwt_required()
def mark_read() -> tuple[Response, int]:
    """Mark notifications as read."""
    data = request.get_json()
    notification_ids = data.get("notification_ids", [])
    if not notification_ids:
        return jsonify({"error": "notification_ids is required"}), 400

    user = get_current_user()
    count = mark_notifications_read(notification_ids, user["id"])
    return jsonify({"message": f"Marked {count} notifications as read"}), 200
