"""Patient API request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PatientCreate(BaseModel):
    """Data required to register a patient."""

    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320)

    @field_validator("name")
    @classmethod
    def require_non_blank_name(cls, value: str) -> str:
        """Reject names consisting only of whitespace."""

        value = value.strip()
        if not value:
            raise ValueError("Name must not be blank.")
        return value

    @field_validator("email")
    @classmethod
    def require_email_address(cls, value: str) -> str:
        """Apply lightweight email validation without an extra dependency."""

        value = value.strip()
        local_part, separator, domain = value.partition("@")
        if not local_part or not separator or not domain or "." not in domain:
            raise ValueError("Email must be a valid email address.")
        return value


class PatientResponse(BaseModel):
    """Patient record returned by the API."""

    id: int
    name: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
