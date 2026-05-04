from typing import Optional

from pydantic import BaseModel, RootModel

from resources.schemas.line_item import LineItemOut


class MessageResponse(BaseModel):
    message: str


class WelcomeResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str


class RefreshAccountIn(BaseModel):
    accountId: Optional[str] = None
    source: Optional[str] = None


class RefreshAllResponse(BaseModel):
    data: list[LineItemOut]


class PaymentMethodOut(BaseModel):
    id: str
    name: str
    type: str
    is_active: bool


class PaymentMethodsResponse(BaseModel):
    data: list[PaymentMethodOut]


class ConnectedAccountsResponse(RootModel[list[dict]]):
    pass
