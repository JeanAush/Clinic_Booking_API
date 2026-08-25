"""Authentication request and response schemas."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Credentials accepted by the login endpoint."""

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class AccessTokenResponse(BaseModel):
    """Bearer access token returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"
