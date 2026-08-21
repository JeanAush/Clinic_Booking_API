"""Schemas for doctor appointment availability."""

from datetime import date, datetime

from pydantic import BaseModel


class DoctorAvailabilityResponse(BaseModel):
    """Available appointment start times for one doctor on one clinic day."""

    doctor_id: int
    date: date
    slots: list[datetime]
