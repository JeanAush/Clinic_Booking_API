"""Patient appointment retrieval operations."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.appointment import Appointment
from app.models.patient import Patient


def get_upcoming_patient_appointments(
    session: Session,
    patient_id: int,
    timezone_name: str,
    now: datetime | None = None,
) -> list[Appointment]:
    """Return a patient's appointments whose starts have not yet passed."""

    patient = session.get(Patient, patient_id)
    if patient is None:
        raise NotFoundError("Patient not found.")

    clinic_timezone = ZoneInfo(timezone_name)
    current_time = (now or datetime.now(clinic_timezone)).astimezone(UTC)
    return list(
        session.scalars(
            select(Appointment)
            .where(
                Appointment.patient_id == patient.id,
                Appointment.start_time > current_time,
            )
            .order_by(Appointment.start_time.asc())
        )
    )
