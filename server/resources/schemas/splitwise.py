from pydantic import BaseModel


class SplitwiseFriendOut(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    name: str
    email: str | None = None


class SplitwiseFriendListResponse(BaseModel):
    data: list[SplitwiseFriendOut]


class SplitwiseExpenseCreateIn(BaseModel):
    description: str
    amount: float
    friend_ids: list[int]
    date: str | None = None
    currency_code: str = "USD"


class SplitwiseExpenseOut(BaseModel):
    id: int | None = None
    description: str | None = None


class SplitwiseExpenseCreateResponse(BaseModel):
    message: str
    data: SplitwiseExpenseOut


class SplitwiseErrorResponse(BaseModel):
    error: str
    details: dict | None = None
