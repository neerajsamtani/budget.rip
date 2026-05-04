from typing import Optional

from pydantic import BaseModel


class LineItemOut(BaseModel):
    id: str
    date: float
    payment_method: str
    description: str
    amount: float
    responsible_party: Optional[str] = None
    notes: Optional[str] = None
    is_manual: bool = False
    event_id: Optional[str] = None


class LineItemListResponse(BaseModel):
    total: float
    data: list[LineItemOut]


class ErrorResponse(BaseModel):
    error: str
