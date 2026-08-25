"""Database queries for patient records."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient import Patient


class PatientRepository:
    """Organize patient persistence operations for a database session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, patient_id: int) -> Patient | None:
        """Return a patient by primary key when it exists."""

        return self._session.get(Patient, patient_id)

    def list_all(self) -> list[Patient]:
        """Return patients in stable primary-key order."""

        return list(self._session.scalars(select(Patient).order_by(Patient.id.asc())))

    def add(self, patient: Patient) -> None:
        """Stage a new patient for the current transaction."""

        self._session.add(patient)
