"""Appointment API request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    """Data required to book a 30-minute appointment."""

    doctor_id: int
    patient_id: int
    start_time: datetime
    end_time: datetime

    @field_validator("start_time", "end_time")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        """Reject ambiguous datetimes before they reach booking logic."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Datetime values must include a timezone offset.")
        return value


class AppointmentResponse(BaseModel):
    """Appointment returned after a successful booking."""

    id: int
    doctor_id: int
    patient_id: int
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
