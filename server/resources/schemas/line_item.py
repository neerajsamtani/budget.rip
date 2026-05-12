from typing import Optional

from pydantic import BaseModel

from resources.schemas._common import ErrorResponse  # noqa: F401


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
