"""Authentication HTTP endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db_session
from app.schemas.auth import AccessTokenResponse, LoginRequest
from app.services.authentication import authenticate

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=AccessTokenResponse, summary="Log in with an account email and password")
def login(credentials: LoginRequest, session: Session = Depends(get_db_session)) -> AccessTokenResponse:
    """Return a Bearer token. Invalid credentials always receive the same error."""

    return AccessTokenResponse(access_token=authenticate(session, credentials.email, credentials.password))
