from typing import List, Optional

from pydantic import BaseModel, Field


class Event(BaseModel):
    id: str
    date: float
    description: str
    amount: float
    line_items: List[str]
    tags: List[str] = Field(default_factory=list)
    is_duplicate_transaction: Optional[bool] = None
