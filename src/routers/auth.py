from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import CurrentUser
from schemas.auth import LoginRequest, LoginResponse, LogoutResponse, SignUpRequest, SignUpResponse, UserResponse
from services.auth_service import AuthService

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
        golf_handicap=user.handicap,
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
