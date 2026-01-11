import logging

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required

logger = logging.getLogger(__name__)

tags_blueprint = Blueprint("tags", __name__)


@tags_blueprint.route("/api/tags", methods=["GET"])
@jwt_required()
def get_all_tags_api() -> tuple[Response, int]:
    from models.database import SessionLocal
    from models.sql_models import Tag

    with SessionLocal.begin() as db:
        tags = db.query(Tag).order_by(Tag.name).all()
        tags_list = [{"id": tag.id, "name": tag.name} for tag in tags]
        return jsonify({"data": tags_list}), 200
