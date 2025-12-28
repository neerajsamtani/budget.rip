import logging
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required

from dao import get_all_tags

logger = logging.getLogger(__name__)

tags_blueprint = Blueprint("tags", __name__)


@tags_blueprint.route("/api/tags", methods=["GET"])
@jwt_required()
def get_all_tags_api() -> tuple[Response, int]:
    try:
        tags: List[Dict[str, Any]] = get_all_tags()
        logger.info(f"Retrieved {len(tags)} tags")
        return jsonify({"data": tags}), 200
    except Exception as e:
        logger.error(f"Error retrieving tags: {e}")
        return jsonify({"error": "Internal server error"}), 500
