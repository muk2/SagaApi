from pydantic import BaseModel, EmailStr
from typing import Optional

class SignUpRequest(BaseModel):
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    email: EmailStr
    password: str
    handicap: Optional[str] = None
    membership: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    role: str = "user"
    email: str
    phone_number: Optional[str] = None
    handicap: Optional[str] = None
    membership: str
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


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    message: str
