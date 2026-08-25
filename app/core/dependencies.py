"""Reusable HTTP dependencies for authentication and role enforcement."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ForbiddenError
from app.database.connection import get_db_session
from app.models.user import User, UserRole
from app.services.authentication import get_authenticated_user

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db_session),
) -> User:
    """Return the authenticated account represented by a Bearer token."""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return get_authenticated_user(session, credentials.credentials)
    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error.detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Create a dependency that permits only the supplied account roles."""

    def check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError("You do not have permission to perform this action.")
        return current_user

    return check_role
