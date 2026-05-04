from pydantic import BaseModel


class TagOut(BaseModel):
    id: str
    name: str


class TagListResponse(BaseModel):
    data: list[TagOut]


class ErrorResponse(BaseModel):
    error: str
