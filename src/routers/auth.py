from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SignUpRequest,
    SignUpResponse,
    UserResponse,
)
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=SignUpResponse)
def signup(data: SignUpRequest, db: Session = Depends(get_db)) -> SignUpResponse:
    """
    Register a new user.

    Creates both a User record (profile data) and a UserAccount record (credentials).
    Returns the created user information without sensitive data.
    """
    service = AuthService(db)
    user, _ = service.signup(data)

    user_response = UserResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        role="user",
        email=data.email,
        phone_number=user.phone_number,
        handicap=user.handicap,
        membership=user.membership
    )

    return SignUpResponse(message="User created successfully", user=user_response)


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """
    Authenticate user and return JWT token.

    Validates credentials against stored password hash.
    Returns a JWT access token for subsequent authenticated requests.
    """
    service = AuthService(db)
    token, user_response = service.login(data)

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=user_response,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(current_user: CurrentUser, db: Session = Depends(get_db)) -> LogoutResponse:
    """
    Logout the current user by invalidating their token.

    Increments the user's token_version, which invalidates all existing tokens.
    Requires a valid JWT token in the Authorization header.
    """
    service = AuthService(db)
    service.logout(current_user.id)
    return LogoutResponse(message="Successfully logged out")


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)) -> ForgotPasswordResponse:
    """
    Initiate password reset flow.

    Generates a reset token and stores it in the database.
    In production, this token should be sent to the user's email.

    Returns success regardless of whether email exists (prevents email enumeration).
    """
    service = AuthService(db)
    service.forgot_password(data)
    return ForgotPasswordResponse(message="Password reset email sent")


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)) -> ResetPasswordResponse:
    """
    Reset user password using a valid reset token.

    Validates the token, checks expiration, updates the password,
    and invalidates all existing JWT tokens for security.
    """
    service = AuthService(db)
    service.reset_password(data)
    return ResetPasswordResponse(message="Password reset successful")
