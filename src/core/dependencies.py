from typing_extensions import Annotated
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.database import get_db
from models.user import User
from services.auth_service import AuthService, decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
security = HTTPBearer(auto_error=False)

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


def get_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that requires the current user to have admin role.
    Raises 403 Forbidden if user is not an admin.
    """
    if not current_user.account or current_user.account.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if token is provided, otherwise return None.
    This allows endpoints to work for both authenticated and unauthenticated users.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        token_data = decode_access_token(token)
        service = AuthService(db)
        service.validate_token_version(token_data.sub, token_data.token_version)
        return service.get_current_user(token_data.sub)
    except:
        return None
    
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(get_admin_user)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)] 