import logging

from apiflask import APIBlueprint
from flask_jwt_extended import jwt_required

from models.database import SessionLocal
from models.sql_models import Tag
from resources._common import JWT_SECURITY
from resources.schemas.tags import TagListResponse

logger = logging.getLogger(__name__)

tags_blueprint = APIBlueprint("tags", __name__)


@tags_blueprint.get("/api/tags")
@tags_blueprint.output(TagListResponse)
@tags_blueprint.doc(security=JWT_SECURITY)
@jwt_required()
def get_all_tags_api():
    with SessionLocal.begin() as db:
        tags = db.query(Tag).order_by(Tag.name).all()
        return TagListResponse(data=[{"id": tag.id, "name": tag.name} for tag in tags])
