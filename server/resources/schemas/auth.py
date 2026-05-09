from typing import Optional

from pydantic import BaseModel


class SignupIn(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class LoginIn(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None


class UserOut(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str


class SignupResponse(BaseModel):
    message: str


class LoginResponse(BaseModel):
    login: bool


class LogoutResponse(BaseModel):
    logout: bool


class ErrorResponse(BaseModel):
    error: str
