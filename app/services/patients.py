"""Patient management operations."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.patient import Patient
from app.schemas.patient import PatientCreate


def create_patient(session: Session, patient_data: PatientCreate) -> Patient:
    """Create a patient, preserving the database's unique-email safeguard."""

    patient = Patient(**patient_data.model_dump())
    session.add(patient)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ConflictError("A patient with this email already exists.") from error
    session.refresh(patient)
    return patient


def get_patient(session: Session, patient_id: int) -> Patient:
    """Return one patient or report that it does not exist."""

    patient = session.get(Patient, patient_id)
    if patient is None:
        raise NotFoundError("Patient not found.")
    return patient


def list_patients(session: Session) -> list[Patient]:
    """Return all patients in stable ID order."""

    return list(session.scalars(select(Patient).order_by(Patient.id.asc())))
