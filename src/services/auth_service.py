from __future__ import annotations
import secrets
from datetime import timezone, datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from core.config import settings
from models.user import User, UserAccount
from repositories.auth_repository import AuthRepository
from schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    SignUpRequest,
    TokenPayload,
    UserResponse,
)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_membership_expiration() -> datetime:
    """Return Dec 31 23:59:59 UTC of the current year."""
    now = datetime.now(timezone.utc)
    return datetime(now.year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)


def is_membership_expired(user) -> bool:
    """Check if a user's membership has expired. Exempt users never expire."""
    if getattr(user, 'membership_exempt', False):
        return False
    if not user.membership_expires_at:
        return False
    return datetime.now(timezone.utc) > user.membership_expires_at


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, token_version: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire, "token_version": token_version}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        return TokenPayload(
            sub=int(user_id),
            exp=payload.get("exp"),
            token_version=payload.get("token_version", 1),
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token",
        ) from e


class AuthService:
    def __init__(self, db: Session):
        self.repo = AuthRepository(db)

    def signup(self, data: SignUpRequest, membership_exempt: bool = False) -> tuple[User, UserAccount]:
        existing = self.repo.get_user_account_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        try:
            user = self.repo.create_user(
                first_name=data.first_name,
                last_name=data.last_name,
                phone_number=data.phone_number,
                handicap=data.handicap,
                membership=data.membership,
                ghin_number=data.ghin_number,
                membership_expires_at=get_membership_expiration(),
                membership_exempt=membership_exempt,
            )

            account = self.repo.create_user_account(
                user_id=user.id,
                email=data.email,
                password_hash=hash_password(data.password),
            )

            self.repo.update_user_account_id(user.id, account.id)
            self.repo.commit()

            return user, account
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {e!s}",
            ) from e

    def login(self, data: LoginRequest) -> tuple[str, UserResponse]:
        account = self.repo.get_user_account_by_email(data.email)

        if not account:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(data.password, account.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        self.repo.update_last_login(account)
        self.repo.commit()

        token = create_access_token(account.user.id, account.token_version)

        user_response = UserResponse(
            id=account.user.id,
            first_name=account.user.first_name,
            last_name=account.user.last_name,
            email=account.email,
            role=account.role or "user",
            handicap=account.user.handicap,
            ghin_number=account.user.ghin_number,
            phone_number=account.user.phone_number,
            membership=account.user.membership,
            membership_expired=is_membership_expired(account.user),
        )

        return token, user_response

    def get_current_user(self, user_id: int) -> User:
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    def validate_token_version(self, user_id: int, token_version: int) -> None:
        account = self.repo.get_user_account_by_user_id(user_id)
        if not account or account.token_version != token_version:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated",
            )

    def logout(self, user_id: int) -> None:
        self.repo.increment_token_version(user_id)
        self.repo.commit()

    def forgot_password(self, data: ForgotPasswordRequest) -> str:
        """
        Initiates password reset flow by sending a reset token via email.
        """
        account = self.repo.get_user_account_by_email(data.email)

        # Don't reveal whether email exists (security best practice)
        if not account:
            # Still return success to prevent email enumeration
            return "If an account exists with that email, you will receive a password reset link."

        # Generate secure reset token
        reset_token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(hours=1)

        self.repo.set_reset_token(account, reset_token, expires)
        self.repo.commit()

        # Send reset email
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        from services.email_service import EmailService
        EmailService().send_password_reset_email(account.email, reset_link)

        return "If an account exists with that email, you will receive a password reset link."

    def reset_password(self, data: ResetPasswordRequest) -> None:
        """
        Resets user password using a valid reset token.
        """
        account = self.repo.get_user_account_by_reset_token(data.token)

        if not account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        # Check if token is expired
        if not account.reset_token_expires or account.reset_token_expires < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        # Update password
        self.repo.update_password(account, hash_password(data.new_password))

        # Clear reset token
        self.repo.clear_reset_token(account)

        # Invalidate all existing tokens for security
        self.repo.increment_token_version(account.user_id)

        self.repo.commit()

