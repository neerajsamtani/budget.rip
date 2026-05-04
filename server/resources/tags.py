import logging

from apiflask import APIBlueprint
from flask_jwt_extended import jwt_required

from models.database import SessionLocal
from models.sql_models import Tag
from resources.schemas.tags import ErrorResponse, TagListResponse

logger = logging.getLogger(__name__)

tags_blueprint = APIBlueprint("tags", __name__)

_SECURITY = [{"jwtCookie": []}]
_ERROR_RESPONSES = {
    400: {"description": "Bad request", "schema": ErrorResponse},
    404: {"description": "Not found", "schema": ErrorResponse},
}


@tags_blueprint.get("/api/tags")
@tags_blueprint.output(TagListResponse)
@tags_blueprint.doc(security=_SECURITY)
@jwt_required()
def get_all_tags_api():
    with SessionLocal.begin() as db:
        tags = db.query(Tag).order_by(Tag.name).all()
        return TagListResponse(data=[{"id": tag.id, "name": tag.name} for tag in tags])
