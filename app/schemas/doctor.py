"""Doctor API request and response schemas."""

from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DoctorCreate(BaseModel):
    """Data required to register a doctor."""

    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320)
    working_start: time
    working_end: time

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

    @model_validator(mode="after")
    def validate_working_hours(self) -> "DoctorCreate":
        """Require a positive daily working window."""

        if self.working_start >= self.working_end:
            raise ValueError("Working start time must be before working end time.")
        return self


class DoctorResponse(BaseModel):
    """Doctor record returned by the API."""

    id: int
    name: str
    email: str
    working_start: time
    working_end: time
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
