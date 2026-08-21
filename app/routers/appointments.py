"""Appointment booking HTTP endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.database.connection import get_db_session
from app.schemas.appointment import AppointmentCancellation, AppointmentCreate, AppointmentResponse
from app.services.appointments import book_appointment, cancel_appointment

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment_data: AppointmentCreate,
    session: Session = Depends(get_db_session),
) -> AppointmentResponse:
    """Book a doctor's currently available 30-minute appointment slot."""

    try:
        return book_appointment(session, appointment_data)
    except ServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_existing_appointment(
    appointment_id: int,
    cancellation_data: AppointmentCancellation,
    session: Session = Depends(get_db_session),
) -> AppointmentResponse:
    """Cancel an appointment and release its slot for future booking."""

    try:
        return cancel_appointment(session, appointment_id, cancellation_data)
    except ServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
