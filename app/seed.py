"""Seed deterministic local development data."""

from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.doctor import Doctor
from app.models.patient import Patient


DOCTOR_DATA = (
    ("Dr. Josephat Wangwe", "josephat.wangwe@clinic.test", time(8, 0), time(16, 0)),
    ("Dr. David Mwangi", "david.mwangi@clinic.test", time(9, 0), time(17, 0)),
    ("Dr. Jean Natwoli", "jean.natwoli@clinic.test", time(8, 30), time(16, 30)),
    ("Dr. Dismas Otieno", "dismas.otieno@clinic.test", time(10, 0), time(18, 0)),
    ("Dr. Francis Juma", "francis.juma@clinic.test", time(7, 30), time(15, 30)),
)

PATIENT_DATA = (
    ("Alice Kamau", "alice.kamau@example.test"),
    ("James Njoroge", "james.njoroge@example.test"),
    ("Mercy Atieno", "mercy.atieno@example.test"),
)


def seed_doctors(session: Session) -> int:
    """Insert any missing predefined doctors and return their count."""

    emails = [doctor[1] for doctor in DOCTOR_DATA]
    existing_emails = set(session.scalars(select(Doctor.email).where(Doctor.email.in_(emails))))
    doctors = [
        Doctor(name=name, email=email, working_start=working_start, working_end=working_end)
        for name, email, working_start, working_end in DOCTOR_DATA
        if email not in existing_emails
    ]
    session.add_all(doctors)
    return len(doctors)


def seed_patients(session: Session) -> int:
    """Insert any missing predefined patients and return their count."""

    emails = [patient[1] for patient in PATIENT_DATA]
    existing_emails = set(session.scalars(select(Patient.email).where(Patient.email.in_(emails))))
    patients = [
        Patient(name=name, email=email)
        for name, email in PATIENT_DATA
        if email not in existing_emails
    ]
    session.add_all(patients)
    return len(patients)


def seed_database() -> tuple[int, int]:
    """Seed missing development records in a single transaction."""

    with SessionLocal.begin() as session:
        created_doctors = seed_doctors(session)
        created_patients = seed_patients(session)
    return created_doctors, created_patients


def main() -> None:
    """Seed the database when run as ``python -m app.seed``."""

    created_doctors, created_patients = seed_database()
    print(f"Seed complete: {created_doctors} doctors and {created_patients} patients created.")


if __name__ == "__main__":
    main()
