"""Database queries for doctor records."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.doctor import Doctor


class DoctorRepository:
    """Organize doctor persistence operations for a database session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, doctor_id: int) -> Doctor | None:
        """Return a doctor by primary key when it exists."""

        return self._session.get(Doctor, doctor_id)

    def list_all(self) -> list[Doctor]:
        """Return doctors in stable primary-key order."""

        return list(self._session.scalars(select(Doctor).order_by(Doctor.id.asc())))

    def add(self, doctor: Doctor) -> None:
        """Stage a new doctor for the current transaction."""

        self._session.add(doctor)
