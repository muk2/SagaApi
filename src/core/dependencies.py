from typing_extensions import Annotated


from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.database import get_db
from models.user import User
from services.auth_service import AuthService, decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that extracts and validates the JWT token from the Authorization header.
    Validates token version to ensure the token hasn't been invalidated by logout.
    Returns the current authenticated user.
    """
    token_data = decode_access_token(token)
    service = AuthService(db)
    service.validate_token_version(token_data.sub, token_data.token_version)
    return service.get_current_user(token_data.sub)


CurrentUser = Annotated[User, Depends(get_current_user)]
