"""Doctor HTTP endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ServiceError
from app.database.connection import get_db_session
from app.schemas.availability import DoctorAvailabilityResponse
from app.services.availability import get_doctor_availability

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("/{doctor_id}/availability", response_model=DoctorAvailabilityResponse)
def get_availability(
    doctor_id: int,
    appointment_date: date = Query(alias="date"),
    session: Session = Depends(get_db_session),
) -> DoctorAvailabilityResponse:
    """List a doctor's available 30-minute slots for a clinic-local date."""

    try:
        slots = get_doctor_availability(
            session, doctor_id, appointment_date, get_settings().timezone
        )
    except ServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    return DoctorAvailabilityResponse(doctor_id=doctor_id, date=appointment_date, slots=slots)
