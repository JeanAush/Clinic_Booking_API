"""Patient HTTP endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ServiceError
from app.database.connection import get_db_session
from app.schemas.appointment import AppointmentResponse
from app.schemas.patient import PatientCreate, PatientResponse
from app.services.patient_appointments import get_upcoming_patient_appointments
from app.services.patients import create_patient, get_patient, list_patients

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_new_patient(
    patient_data: PatientCreate,
    session: Session = Depends(get_db_session),
) -> PatientResponse:
    """Register a patient."""

    try:
        return create_patient(session, patient_data)
    except ServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("", response_model=list[PatientResponse])
def list_registered_patients(session: Session = Depends(get_db_session)) -> list[PatientResponse]:
    """List registered patients in creation order."""

    return list_patients(session)


@router.get("/{patient_id}", response_model=PatientResponse)
def get_registered_patient(
    patient_id: int,
    session: Session = Depends(get_db_session),
) -> PatientResponse:
    """Retrieve one patient by ID."""

    try:
        return get_patient(session, patient_id)
    except ServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error


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
