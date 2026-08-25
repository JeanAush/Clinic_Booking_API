"""Password hashing and JWT primitives used by authentication services."""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.models.user import User, UserRole


def hash_password(password: str) -> str:
    """Return a bcrypt hash without retaining the supplied plaintext password."""

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a plaintext password matches its bcrypt hash."""

    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user: User) -> str:
    """Create a signed, expiring access token for an authenticated account."""

    settings = get_settings()
    secret = _jwt_secret()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    claims = {"sub": str(user.id), "role": user.role.value, "exp": expires_at}
    return jwt.encode(claims, secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> tuple[int, UserRole]:
    """Validate a token and return its subject and role claims."""

    settings = get_settings()
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[settings.jwt_algorithm])
        return int(payload["sub"]), UserRole(payload["role"])
    except (InvalidTokenError, KeyError, TypeError, ValueError) as error:
        raise AuthenticationError("Could not validate credentials.") from error


def _jwt_secret() -> str:
    """Return the configured signing secret or fail safely if it is missing."""

    secret = get_settings().jwt_secret
    if secret is None:
        raise RuntimeError("CLINIC_JWT_SECRET must be configured for authentication.")
    return secret
