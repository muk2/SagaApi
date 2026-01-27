from __future__ import annotations
from datetime import timezone, datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from core.config import settings
from models.user import User, UserAccount
from repositories.auth_repository import AuthRepository
from schemas.auth import LoginRequest, SignUpRequest, TokenPayload, UserResponse

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


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

    def signup(self, data: SignUpRequest) -> tuple[User, UserAccount]:
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
                handicap=data.golf_handicap,
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
            role=account.role or "user",
            golf_handicap=account.user.handicap,
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
