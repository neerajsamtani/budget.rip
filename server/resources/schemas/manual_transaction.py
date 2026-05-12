from pydantic import BaseModel

from resources.schemas._common import ErrorResponse, MessageResponse  # noqa: F401


class ManualTransactionCreateIn(BaseModel):
    date: str
    person: str
    description: str
    amount: float
    payment_method_id: str


class ManualTransactionCreateResponse(BaseModel):
    message: str
    transaction_id: str
