from pydantic import BaseModel


class LineItem(BaseModel):
    id: str
    date: float
    responsible_party: str
    payment_method: str
    description: str
    amount: float
