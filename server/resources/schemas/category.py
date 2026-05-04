from typing import Optional

from pydantic import BaseModel


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


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str
