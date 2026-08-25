"""Doctor management operations."""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.doctor import Doctor
from app.repositories.doctors import DoctorRepository
from app.schemas.doctor import DoctorCreate
from app.services.transactions import commit_or_raise_conflict


def create_doctor(session: Session, doctor_data: DoctorCreate) -> Doctor:
    """Create a doctor, preserving the database's unique-email safeguard."""

    doctor = Doctor(**doctor_data.model_dump())
    DoctorRepository(session).add(doctor)
    commit_or_raise_conflict(session, "A doctor with this email already exists.")
    session.refresh(doctor)
    return doctor


def get_doctor(session: Session, doctor_id: int) -> Doctor:
    """Return one doctor or report that it does not exist."""

    doctor = DoctorRepository(session).get(doctor_id)
    if doctor is None:
        raise NotFoundError("Doctor not found.")
    return doctor


def list_doctors(session: Session) -> list[Doctor]:
    """Return all doctors in stable ID order."""

    return DoctorRepository(session).list_all()
