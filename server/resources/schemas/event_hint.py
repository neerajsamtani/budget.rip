from typing import Optional

from pydantic import BaseModel


class EventHintOut(BaseModel):
    id: str
    name: str
    cel_expression: str
    prefill_name: str
    prefill_category: Optional[str] = None
    prefill_category_id: Optional[str] = None
    display_order: int
    is_active: bool


class EventHintCreateIn(BaseModel):
    name: str
    cel_expression: str
    prefill_name: str
    prefill_category_id: Optional[str] = None
    is_active: Optional[bool] = True


class EventHintUpdateIn(BaseModel):
    name: Optional[str] = None
    cel_expression: Optional[str] = None
    prefill_name: Optional[str] = None
    prefill_category_id: Optional[str] = None
    is_active: Optional[bool] = None


class ReorderIn(BaseModel):
    hint_ids: list[str]


class EvaluateIn(BaseModel):
    line_item_ids: list[str]


class ValidateCelIn(BaseModel):
    cel_expression: str


class EventHintSuggestionOut(BaseModel):
    name: str
    category: Optional[str] = None
    matched_hint_id: str
    matched_hint_name: str


class EvaluateData(BaseModel):
    suggestion: Optional[EventHintSuggestionOut] = None


class ValidateCelData(BaseModel):
    is_valid: bool
    error: Optional[str] = None


class EventHintListResponse(BaseModel):
    data: list[EventHintOut]


class EventHintSingleResponse(BaseModel):
    data: EventHintOut


class EvaluateResponse(BaseModel):
    data: EvaluateData


class ValidateCelResponse(BaseModel):
    data: ValidateCelData


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str
