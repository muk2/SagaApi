from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User, UserAccount


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_account_by_email(self, email: str) -> UserAccount | None:
        stmt = select(UserAccount).where(UserAccount.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_account_by_user_id(self, user_id: int) -> UserAccount | None:
        stmt = select(UserAccount).where(UserAccount.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def increment_token_version(self, user_id: int) -> None:
        account = self.get_user_account_by_user_id(user_id)
        if account:
            account.token_version += 1

    def create_user(
        self,
        first_name: str,
        last_name: str,
        phone_number: str | None,
        handicap: int | None,
    ) -> User:
        user = User(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            handicap=handicap,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def create_user_account(
        self,
        user_id: int,
        email: str,
        password_hash: str,
    ) -> UserAccount:
        account = UserAccount(
            user_id=user_id,
            email=email,
            password_hash=password_hash,
        )
        self.db.add(account)
        self.db.flush()
        return account

    def update_user_account_id(self, user_id: int, account_id: int) -> None:
        user = self.get_user_by_id(user_id)
        if user:
            user.user_account_id = account_id

    def update_last_login(self, account: UserAccount) -> None:
        account.last_logged_in = datetime.now()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def set_reset_token(self, account: UserAccount, token: str, expires: datetime) -> None:
        account.reset_token = token
        account.reset_token_expires = expires

    def get_user_account_by_reset_token(self, token: str) -> UserAccount | None:
        stmt = select(UserAccount).where(UserAccount.reset_token == token)
        return self.db.execute(stmt).scalar_one_or_none()

    def clear_reset_token(self, account: UserAccount) -> None:
        account.reset_token = None
        account.reset_token_expires = None

    def update_password(self, account: UserAccount, password_hash: str) -> None:
        account.password_hash = password_hash
