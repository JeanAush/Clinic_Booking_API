"""Doctor management operations."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.doctor import Doctor
from app.schemas.doctor import DoctorCreate


def create_doctor(session: Session, doctor_data: DoctorCreate) -> Doctor:
    """Create a doctor, preserving the database's unique-email safeguard."""

    doctor = Doctor(**doctor_data.model_dump())
    session.add(doctor)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ConflictError("A doctor with this email already exists.") from error
    session.refresh(doctor)
    return doctor


def get_doctor(session: Session, doctor_id: int) -> Doctor:
    """Return one doctor or report that it does not exist."""

    doctor = session.get(Doctor, doctor_id)
    if doctor is None:
        raise NotFoundError("Doctor not found.")
    return doctor


def list_doctors(session: Session) -> list[Doctor]:
    """Return all doctors in stable ID order."""

    return list(session.scalars(select(Doctor).order_by(Doctor.id.asc())))
