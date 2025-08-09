from typing import Optional

from pydantic import BaseModel


class CashTransaction(BaseModel):
    id: Optional[str] = None
    date: float
    person: str
    description: str
    amount: int
