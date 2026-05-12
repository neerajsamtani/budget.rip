from typing import Optional

from pydantic import BaseModel

from resources.schemas._common import ErrorResponse, MessageResponse  # noqa: F401


class CategoryOut(BaseModel):
    id: str
    name: str


class CategoryCreateIn(BaseModel):
    name: str


class CategoryUpdateIn(BaseModel):
    name: Optional[str] = None


class CategoryListResponse(BaseModel):
    data: list[CategoryOut]


class CategorySingleResponse(BaseModel):
    data: CategoryOut
