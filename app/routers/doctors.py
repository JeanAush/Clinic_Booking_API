"""Doctor HTTP endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.connection import get_db_session
from app.schemas.availability import DoctorAvailabilityResponse
from app.schemas.doctor import DoctorCreate, DoctorResponse
from app.services.availability import get_doctor_availability
from app.services.doctors import create_doctor, get_doctor, list_doctors

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.post("", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
def create_new_doctor(
    doctor_data: DoctorCreate,
    session: Session = Depends(get_db_session),
) -> DoctorResponse:
    """Register a doctor with a daily working window."""

    return create_doctor(session, doctor_data)


@router.get("", response_model=list[DoctorResponse])
def list_registered_doctors(session: Session = Depends(get_db_session)) -> list[DoctorResponse]:
    """List registered doctors in creation order."""

    return list_doctors(session)


@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_registered_doctor(
    doctor_id: int,
    session: Session = Depends(get_db_session),
) -> DoctorResponse:
    """Retrieve one doctor by ID."""

    return get_doctor(session, doctor_id)


@router.get("/{doctor_id}/availability", response_model=DoctorAvailabilityResponse)
def get_availability(
    doctor_id: int,
    appointment_date: date = Query(alias="date"),
    session: Session = Depends(get_db_session),
) -> DoctorAvailabilityResponse:
    """List a doctor's available 30-minute slots for a clinic-local date."""

    slots = get_doctor_availability(session, doctor_id, appointment_date, get_settings().timezone)
    return DoctorAvailabilityResponse(doctor_id=doctor_id, date=appointment_date, slots=slots)
