from pydantic import BaseModel, EmailStr
from typing import Optional

class SignUpRequest(BaseModel):
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    email: EmailStr
    password: str
    golf_handicap: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    role: str = "user"
    golf_handicap: Optional[int] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SignUpResponse(BaseModel):
    message: str
    user: UserResponse


class TokenPayload(BaseModel):
    sub: int
    exp: Optional[int] = None
    token_version: int = 1


class LogoutResponse(BaseModel):
    message: str
