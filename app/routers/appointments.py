"""Appointment booking HTTP endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.database.connection import get_db_session
from app.models.user import User, UserRole
from app.schemas.appointment import (
    AppointmentCancellation,
    AppointmentCreate,
    AppointmentReschedule,
    AppointmentResponse,
)
from app.services.appointments import book_appointment, cancel_appointment, reschedule_appointment

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book an appointment for the authenticated patient",
)
def create_appointment(
    appointment_data: AppointmentCreate,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PATIENT)),
) -> AppointmentResponse:
    """Book a doctor's currently available 30-minute appointment slot."""

    return book_appointment(session, appointment_data, current_user)


@router.patch(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
    summary="Cancel an appointment you own or are assigned to",
)
def cancel_existing_appointment(
    appointment_id: int,
    cancellation_data: AppointmentCancellation,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> AppointmentResponse:
    """Cancel an appointment and release its slot for future booking."""

    return cancel_appointment(session, appointment_id, cancellation_data, current_user)


@router.patch(
    "/{appointment_id}/reschedule",
    response_model=AppointmentResponse,
    summary="Reschedule an appointment you own or are assigned to",
)
def reschedule_existing_appointment(
    appointment_id: int,
    reschedule_data: AppointmentReschedule,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> AppointmentResponse:
    """Move an active appointment to a different valid slot."""

    return reschedule_appointment(session, appointment_id, reschedule_data, current_user)
