"""Patient HTTP endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ServiceError
from app.database.connection import get_db_session
from app.schemas.appointment import AppointmentResponse
from app.services.patient_appointments import get_upcoming_patient_appointments

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/{patient_id}/appointments", response_model=list[AppointmentResponse])
def list_upcoming_appointments(
    patient_id: int,
    session: Session = Depends(get_db_session),
) -> list[AppointmentResponse]:
    """List a patient's upcoming appointments in chronological order."""

    try:
        return get_upcoming_patient_appointments(session, patient_id, get_settings().timezone)
    except ServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
