"""Authentication and token validation tests."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole


def create_account(session: Session, role: UserRole = UserRole.ADMIN) -> tuple[User, str]:
    """Persist a standalone test account and return it with its plaintext test password."""

    password = "correct-horse-battery-staple"
    user = User(
        email=f"account-{uuid4().hex}@example.test",
        password_hash=hash_password(password),
        role=role,
    )
    session.add(user)
    session.flush()
    return user, password


def test_passwords_are_hashed_and_verified() -> None:
    """Password helpers never retain the supplied plaintext password."""

    password_hash = hash_password("safe-password")

    assert password_hash != "safe-password"
    assert verify_password("safe-password", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_login_returns_a_bearer_token(client: TestClient, session: Session) -> None:
    """Valid credentials receive a signed access token."""

    user, password = create_account(session)
    response = client.post("/auth/login", json={"email": user.email, "password": password})

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_does_not_disclose_invalid_email_or_password(client: TestClient, session: Session) -> None:
    """Unknown accounts and bad passwords return the same error."""

    user, _ = create_account(session)
    unknown = client.post("/auth/login", json={"email": "unknown@example.test", "password": "bad"})
    incorrect = client.post("/auth/login", json={"email": user.email, "password": "bad"})

    assert unknown.status_code == incorrect.status_code == 401
    assert unknown.json()["detail"] == incorrect.json()["detail"] == "Invalid email or password."


def test_protected_endpoint_rejects_missing_invalid_and_expired_tokens(client: TestClient) -> None:
    """Protected endpoints reject absent, malformed, and expired bearer tokens."""

    client.headers.pop("Authorization")
    missing = client.get("/patients")
    invalid = client.get("/patients", headers={"Authorization": "Bearer invalid"})
    expired_token = jwt.encode(
        {"sub": "1", "role": UserRole.ADMIN.value, "exp": datetime.now(UTC) - timedelta(minutes=1)},
        get_settings().jwt_secret,
        algorithm=get_settings().jwt_algorithm,
    )
    expired = client.get("/patients", headers={"Authorization": f"Bearer {expired_token}"})

    assert missing.status_code == invalid.status_code == expired.status_code == 401
