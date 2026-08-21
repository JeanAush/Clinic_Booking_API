"""Reusable appointment timing and working-hours validation."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.exceptions import ValidationError
from app.models.doctor import Doctor

APPOINTMENT_DURATION = timedelta(minutes=30)
MINIMUM_BOOKING_NOTICE = timedelta(hours=1)


def validate_appointment_schedule(
    doctor: Doctor,
    start_time: datetime,
    end_time: datetime,
    timezone_name: str,
    now: datetime | None = None,
) -> None:
    """Validate the universal timing rules for a doctor's appointment."""

    clinic_timezone = ZoneInfo(timezone_name)
    current_time = now or datetime.now(clinic_timezone)
    if start_time <= current_time:
        raise ValidationError("Appointment start time must be in the future.")
    if start_time < current_time + MINIMUM_BOOKING_NOTICE:
        raise ValidationError("Appointments must be booked at least one hour in advance.")
    if end_time - start_time != APPOINTMENT_DURATION:
        raise ValidationError("Appointment duration must be exactly 30 minutes.")

    local_start = start_time.astimezone(clinic_timezone)
    local_end = end_time.astimezone(clinic_timezone)
    if local_start.minute not in (0, 30) or local_start.second or local_start.microsecond:
        raise ValidationError("Appointment start time must be on a 30-minute boundary.")
    if local_start.date() != local_end.date():
        raise ValidationError("Appointment must fall within a single clinic working day.")
    if local_start.time().replace(tzinfo=None) < doctor.working_start:
        raise ValidationError("Appointment is outside the doctor's working hours.")
    if local_end.time().replace(tzinfo=None) > doctor.working_end:
        raise ValidationError("Appointment is outside the doctor's working hours.")
