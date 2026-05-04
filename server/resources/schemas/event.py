from typing import Optional

from pydantic import BaseModel

from resources.schemas.line_item import LineItemOut  # noqa: F401


class EventOut(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    amount: float
    date: float
    line_items: list[str]
    tags: list[str] = []
    is_duplicate_transaction: bool = False


class EventListResponse(BaseModel):
    total: float
    data: list[EventOut]


class EventLineItemsResponse(BaseModel):
    data: list[LineItemOut]


class EventCreateIn(BaseModel):
    name: str
    category: Optional[str] = None
    date: Optional[str] = None
    line_items: list[str]
    tags: list[str] = []
    is_duplicate_transaction: bool = False


class EventUpdateIn(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    date: Optional[str] = None
    line_items: list[str]
    tags: list[str] = []
    is_duplicate_transaction: bool = False


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str
