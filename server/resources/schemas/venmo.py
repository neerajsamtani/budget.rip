from pydantic import BaseModel


class RefreshResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str
