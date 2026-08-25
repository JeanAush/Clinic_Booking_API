"""Patient HTTP endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_current_user, require_roles
from app.database.connection import get_db_session
from app.schemas.appointment import AppointmentResponse
from app.schemas.patient import PatientCreate, PatientResponse
from app.services.patient_appointments import get_upcoming_patient_appointments
from app.services.patients import create_patient, get_patient, list_patients
from app.models.user import User, UserRole

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED, summary="Admin: register a patient")
def create_new_patient(
    patient_data: PatientCreate,
    session: Session = Depends(get_db_session),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> PatientResponse:
    """Register a patient."""

    return create_patient(session, patient_data)


@router.get("", response_model=list[PatientResponse], summary="Admin: list registered patients")
def list_registered_patients(
    session: Session = Depends(get_db_session),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[PatientResponse]:
    """List registered patients in creation order."""

    return list_patients(session)


@router.get("/{patient_id}", response_model=PatientResponse, summary="Admin: retrieve a patient")
def get_registered_patient(
    patient_id: int,
    session: Session = Depends(get_db_session),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> PatientResponse:
    """Retrieve one patient by ID."""

    return get_patient(session, patient_id)


@router.get(
    "/{patient_id}/appointments",
    response_model=list[AppointmentResponse],
    summary="List the authenticated patient's upcoming appointments",
)
def list_upcoming_appointments(
    patient_id: int,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PATIENT)),
) -> list[AppointmentResponse]:
    """List a patient's upcoming appointments in chronological order."""

    return get_upcoming_patient_appointments(session, patient_id, get_settings().timezone, current_user)
