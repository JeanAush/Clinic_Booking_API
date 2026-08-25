"""Authentication workflows independent of HTTP transport."""

from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, decode_access_token, verify_password
from app.models.user import User
from app.repositories.users import UserRepository


def authenticate(session: Session, email: str, password: str) -> str:
    """Verify credentials and return a signed access token on success."""

    user = UserRepository(session).get_by_email(email.strip())
    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password.")
    return create_access_token(user)


def get_authenticated_user(session: Session, token: str) -> User:
    """Resolve a valid token to its current persisted account."""

    user_id, token_role = decode_access_token(token)
    user = UserRepository(session).get(user_id)
    if user is None or user.role != token_role:
        raise AuthenticationError("Could not validate credentials.")
    return user
