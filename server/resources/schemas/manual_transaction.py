from pydantic import BaseModel


class ManualTransactionCreateIn(BaseModel):
    date: str
    person: str
    description: str
    amount: float
    payment_method_id: str


class ManualTransactionCreateResponse(BaseModel):
    message: str
    transaction_id: str


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str
