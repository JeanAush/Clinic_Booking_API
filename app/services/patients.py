"""Patient management operations."""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.patient import Patient
from app.repositories.patients import PatientRepository
from app.schemas.patient import PatientCreate
from app.services.transactions import commit_or_raise_conflict


def create_patient(session: Session, patient_data: PatientCreate) -> Patient:
    """Create a patient, preserving the database's unique-email safeguard."""

    patient = Patient(**patient_data.model_dump())
    PatientRepository(session).add(patient)
    commit_or_raise_conflict(session, "A patient with this email already exists.")
    session.refresh(patient)
    return patient


def get_patient(session: Session, patient_id: int) -> Patient:
    """Return one patient or report that it does not exist."""

    patient = PatientRepository(session).get(patient_id)
    if patient is None:
        raise NotFoundError("Patient not found.")
    return patient


def list_patients(session: Session) -> list[Patient]:
    """Return all patients in stable ID order."""

    return PatientRepository(session).list_all()
