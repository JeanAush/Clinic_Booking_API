"""Appointment booking operations."""

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError
from app.models.appointment import Appointment, AppointmentStatus
from app.repositories.appointments import AppointmentRepository
from app.repositories.doctors import DoctorRepository
from app.repositories.patients import PatientRepository
from app.schemas.appointment import AppointmentCancellation, AppointmentCreate, AppointmentReschedule
from app.models.user import User
from app.services.authorization import ensure_appointment_access, ensure_patient_can_book
from app.services.appointment_rules import validate_appointment_schedule
from app.services.transactions import commit_or_raise_conflict

ACTIVE_SLOT_CONSTRAINT = "ex_appointments_active_doctor_time"


def book_appointment(session: Session, appointment_data: AppointmentCreate, user: User) -> Appointment:
    """Validate and persist a booking, including database conflict protection."""

    ensure_patient_can_book(user, appointment_data.patient_id)
    doctor = DoctorRepository(session).get(appointment_data.doctor_id)
    if doctor is None:
        raise NotFoundError("Doctor not found.")

    patient = PatientRepository(session).get(appointment_data.patient_id)
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
    AppointmentRepository(session).add(appointment)
    commit_or_raise_conflict(
        session,
        "This doctor is no longer available for the selected slot.",
        ACTIVE_SLOT_CONSTRAINT,
    )

    session.refresh(appointment)
    return appointment


def cancel_appointment(
    session: Session,
    appointment_id: int,
    cancellation_data: AppointmentCancellation,
    user: User,
) -> Appointment:
    """Cancel an active appointment and record why it was cancelled."""

    appointment = AppointmentRepository(session).get(appointment_id)
    if appointment is None:
        raise NotFoundError("Appointment not found.")
    ensure_appointment_access(user, appointment)
    if appointment.status == AppointmentStatus.CANCELLED:
        raise ConflictError("Appointment is already cancelled.")

    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancellation_reason = cancellation_data.reason
    session.commit()
    session.refresh(appointment)
    return appointment


def reschedule_appointment(
    session: Session,
    appointment_id: int,
    reschedule_data: AppointmentReschedule,
    user: User,
) -> Appointment:
    """Move an active appointment to a valid, unoccupied slot atomically."""

    appointment = AppointmentRepository(session).get(appointment_id)
    if appointment is None:
        raise NotFoundError("Appointment not found.")
    ensure_appointment_access(user, appointment)
    if appointment.status == AppointmentStatus.CANCELLED:
        raise ConflictError("Cancelled appointments cannot be rescheduled.")

    doctor = DoctorRepository(session).get(appointment.doctor_id)
    if doctor is None:
        raise NotFoundError("Doctor not found.")
    validate_appointment_schedule(
        doctor,
        reschedule_data.start_time,
        reschedule_data.end_time,
        get_settings().timezone,
    )

    appointment.start_time = reschedule_data.start_time
    appointment.end_time = reschedule_data.end_time
    commit_or_raise_conflict(
        session,
        "This doctor is no longer available for the selected slot.",
        ACTIVE_SLOT_CONSTRAINT,
    )

    session.refresh(appointment)
    return appointment
