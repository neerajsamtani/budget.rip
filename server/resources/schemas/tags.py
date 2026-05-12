from pydantic import BaseModel

from resources.schemas._common import ErrorResponse  # noqa: F401


class TagOut(BaseModel):
    id: str
    name: str


class TagListResponse(BaseModel):
    data: list[TagOut]
