"""Appointment booking HTTP endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.database.connection import get_db_session
from app.schemas.appointment import AppointmentCreate, AppointmentResponse
from app.services.appointments import book_appointment

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
