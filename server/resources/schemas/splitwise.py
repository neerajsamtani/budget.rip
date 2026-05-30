from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class SplitwiseFriendOut(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    name: str
    email: str | None = None


class SplitwiseFriendListResponse(BaseModel):
    data: list[SplitwiseFriendOut]


class SplitwiseCurrentUserOut(BaseModel):
    id: int


class SplitwiseCurrentUserResponse(BaseModel):
    data: SplitwiseCurrentUserOut


class SplitwiseExpenseCreateIn(BaseModel):
    description: str
    amount: Decimal
    friend_ids: list[int]
    split_method: Literal["equal", "custom"] = "equal"
    owed_shares: dict[str, Decimal] | None = None
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
