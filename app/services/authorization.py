"""Business authorization rules for appointment ownership."""

from app.core.exceptions import ForbiddenError
from app.models.appointment import Appointment
from app.models.user import User, UserRole


def ensure_patient_can_book(user: User, patient_id: int) -> None:
    """Allow a patient to book only for their own profile; admins may manage all."""

    if user.role == UserRole.ADMIN:
        return
    if user.role != UserRole.PATIENT or user.patient_id != patient_id:
        raise ForbiddenError("You may only book appointments for your own patient profile.")


def ensure_appointment_access(user: User, appointment: Appointment) -> None:
    """Allow admins and the appointment's own patient or doctor to manage it."""

    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.PATIENT and user.patient_id == appointment.patient_id:
        return
    if user.role == UserRole.DOCTOR and user.doctor_id == appointment.doctor_id:
        return
    raise ForbiddenError("You do not have permission to access this appointment.")


def ensure_patient_appointments_access(user: User, patient_id: int) -> None:
    """Allow a patient to read only their own appointment listing; admins may read all."""

    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.PATIENT and user.patient_id == patient_id:
        return
    raise ForbiddenError("You may only access your own appointment information.")
