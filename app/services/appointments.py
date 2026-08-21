"""Appointment booking operations."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.schemas.appointment import AppointmentCancellation, AppointmentCreate
from app.services.appointment_rules import validate_appointment_schedule

ACTIVE_SLOT_CONSTRAINT = "ex_appointments_active_doctor_time"


def book_appointment(session: Session, appointment_data: AppointmentCreate) -> Appointment:
    """Validate and persist a booking, including database conflict protection."""

    doctor = session.get(Doctor, appointment_data.doctor_id)
    if doctor is None:
        raise NotFoundError("Doctor not found.")

    patient = session.get(Patient, appointment_data.patient_id)
    if patient is None:
        raise NotFoundError("Patient not found.")

    validate_appointment_schedule(
        doctor,
        appointment_data.start_time,
        appointment_data.end_time,
        get_settings().timezone,
    )
    appointment = Appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        start_time=appointment_data.start_time,
        end_time=appointment_data.end_time,
        status=AppointmentStatus.BOOKED,
    )
    session.add(appointment)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        if _is_active_slot_conflict(error):
            raise ConflictError("This doctor is no longer available for the selected slot.") from error
        raise

    session.refresh(appointment)
    return appointment


def cancel_appointment(
    session: Session,
    appointment_id: int,
    cancellation_data: AppointmentCancellation,
) -> Appointment:
    """Cancel an active appointment and record why it was cancelled."""

    appointment = session.get(Appointment, appointment_id)
    if appointment is None:
        raise NotFoundError("Appointment not found.")
    if appointment.status == AppointmentStatus.CANCELLED:
        raise ConflictError("Appointment is already cancelled.")

    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancellation_reason = cancellation_data.reason
    session.commit()
    session.refresh(appointment)
    return appointment


def _is_active_slot_conflict(error: IntegrityError) -> bool:
    """Identify the PostgreSQL exclusion constraint behind a booking conflict."""

    diagnostics = getattr(error.orig, "diag", None)
    return getattr(diagnostics, "constraint_name", None) == ACTIVE_SLOT_CONSTRAINT
