from typing import Optional

from pydantic import BaseModel, RootModel

from resources.schemas._common import ErrorResponse, MessageResponse  # noqa: F401
from resources.schemas.line_item import LineItemOut


class WelcomeResponse(BaseModel):
    message: str


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
