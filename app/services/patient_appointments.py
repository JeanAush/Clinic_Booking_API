"""Patient appointment retrieval operations."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.appointment import Appointment
from app.repositories.appointments import AppointmentRepository
from app.repositories.patients import PatientRepository
from app.models.user import User
from app.services.authorization import ensure_patient_appointments_access
from app.utils.timezones import clinic_now, utc_time


def get_upcoming_patient_appointments(
    session: Session,
    patient_id: int,
    timezone_name: str,
    user: User,
    now: datetime | None = None,
) -> list[Appointment]:
    """Return a patient's appointments whose starts have not yet passed."""

    ensure_patient_appointments_access(user, patient_id)
    patient = PatientRepository(session).get(patient_id)
    if patient is None:
        raise NotFoundError("Patient not found.")

    return AppointmentRepository(session).list_upcoming_for_patient(
        patient.id,
        utc_time(clinic_now(timezone_name, now)),
    )
