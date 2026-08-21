"""Doctor appointment availability operations."""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.services.appointment_rules import APPOINTMENT_DURATION, MINIMUM_BOOKING_NOTICE


def get_doctor_availability(
    session: Session,
    doctor_id: int,
    appointment_date: date,
    timezone_name: str,
    now: datetime | None = None,
) -> list[datetime]:
    """Return unbooked, bookable 30-minute clinic-local slots for a doctor."""

    doctor = session.get(Doctor, doctor_id)
    if doctor is None:
        raise NotFoundError("Doctor not found.")

    clinic_timezone = ZoneInfo(timezone_name)
    current_time = (now or datetime.now(clinic_timezone)).astimezone(clinic_timezone)
    day_start = datetime.combine(appointment_date, datetime.min.time(), tzinfo=clinic_timezone)
    day_end = day_start + timedelta(days=1)

    booked_appointments = session.scalars(
        select(Appointment).where(
            Appointment.doctor_id == doctor.id,
            Appointment.status == AppointmentStatus.BOOKED,
            Appointment.start_time < day_end.astimezone(UTC),
            Appointment.end_time > day_start.astimezone(UTC),
        )
    ).all()
    booked_ranges = [
        (appointment.start_time.astimezone(UTC), appointment.end_time.astimezone(UTC))
        for appointment in booked_appointments
    ]

    slot_start = datetime.combine(appointment_date, doctor.working_start, tzinfo=clinic_timezone)
    working_end = datetime.combine(appointment_date, doctor.working_end, tzinfo=clinic_timezone)
    minimum_today_start = current_time + MINIMUM_BOOKING_NOTICE
    available_slots: list[datetime] = []

    while slot_start + APPOINTMENT_DURATION <= working_end:
        slot_end = slot_start + APPOINTMENT_DURATION
        slot_start_utc = slot_start.astimezone(UTC)
        slot_end_utc = slot_end.astimezone(UTC)
        is_booked = any(
            slot_start_utc < booked_end and slot_end_utc > booked_start
            for booked_start, booked_end in booked_ranges
        )
        is_past = slot_start < current_time
        lacks_notice = appointment_date == current_time.date() and slot_start < minimum_today_start

        if not is_booked and not is_past and not lacks_notice:
            available_slots.append(slot_start)
        slot_start = slot_end

    return available_slots
