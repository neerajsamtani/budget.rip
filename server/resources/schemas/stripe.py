from pydantic import BaseModel, RootModel


class RefreshResponse(BaseModel):
    message: str


class FcSessionResponse(BaseModel):
    clientSecret: str


# RootModel is used because the request body is a bare JSON array, not an object.
class CreateAccountsIn(RootModel[list[dict]]):
    pass


class CreateAccountsResponse(BaseModel):
    data: list[dict]


class GetAccountsResponse(BaseModel):
    accounts: list[dict]


class AccountBalanceOut(BaseModel):
    id: str
    name: str
    balance: float
    currency: str
    as_of: int | None
    status: str
    can_relink: bool


# RootModel is used because the response is a dict keyed by dynamic account IDs, not a fixed-field object.
class AccountsAndBalancesResponse(RootModel[dict[str, AccountBalanceOut]]):
    pass


class SubscribeToAccountIn(BaseModel):
    account_id: str


class SubscribeStatusResponse(BaseModel):
    status: str


class RefreshAccountResponse(BaseModel):
    data: str


class RelinkResponse(BaseModel):
    relink_required: bool | None = None
    clientSecret: str | None = None


class ErrorResponse(BaseModel):
    error: str
