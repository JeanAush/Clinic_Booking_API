"""Fixtures for integration tests against the configured PostgreSQL schema."""

from collections.abc import Generator
from datetime import UTC, date, datetime, time, timedelta
import os
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

os.environ.setdefault("CLINIC_JWT_SECRET", "test-only-secret-that-is-long-enough-for-jwt")

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.database.connection import get_db_session
from app.main import app
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User, UserRole

TEST_ADMIN_PASSWORD_HASH = "$2b$12$FzLwx7uihcem7uiS3DjwcufcS7ssuFmKrMix5yPzx7KFT.BpFPqSa"


@pytest.fixture
def session() -> Generator[Session, None, None]:
    """Provide an isolated transaction that is rolled back after each test."""

    database_url = get_settings().database_url
    if database_url is None:
        pytest.fail("CLINIC_DATABASE_URL must be configured before running tests.")

    engine = create_engine(database_url)
    connection = engine.connect()
    transaction = connection.begin()
    database_session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield database_session
    finally:
        database_session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    """Provide an authenticated admin client using the test transaction."""

    app.dependency_overrides[get_db_session] = lambda: session
    admin = User(
        email=f"admin-{uuid4().hex}@example.test",
        password_hash=TEST_ADMIN_PASSWORD_HASH,
        role=UserRole.ADMIN,
    )
    session.add(admin)
    session.flush()
    with TestClient(app) as test_client:
        test_client.headers.update(authorization_header(admin))
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def doctor(session: Session) -> Doctor:
    """Create a doctor with an 08:00–17:00 local working day."""

    identifier = uuid4().hex
    doctor_record = Doctor(
        name="Test Doctor",
        email=f"doctor-{identifier}@example.test",
        working_start=time(8, 0),
        working_end=time(17, 0),
    )
    session.add(doctor_record)
    session.flush()
    return doctor_record


@pytest.fixture
def patient(session: Session) -> Patient:
    """Create a patient for a booking request."""

    patient_record = Patient(name="Test Patient", email=f"patient-{uuid4().hex}@example.test")
    session.add(patient_record)
    session.flush()
    return patient_record


@pytest.fixture
def doctor_user(session: Session, doctor: Doctor) -> User:
    """Create an authenticated account linked to the doctor fixture."""

    user = User(
        email=f"doctor-account-{uuid4().hex}@example.test",
        password_hash=hash_password("doctor-password"),
        role=UserRole.DOCTOR,
        doctor_id=doctor.id,
    )
    session.add(user)
    session.flush()
    return user


@pytest.fixture
def patient_user(session: Session, patient: Patient) -> User:
    """Create an authenticated account linked to the patient fixture."""

    user = User(
        email=f"patient-account-{uuid4().hex}@example.test",
        password_hash=hash_password("patient-password"),
        role=UserRole.PATIENT,
        patient_id=patient.id,
    )
    session.add(user)
    session.flush()
    return user


def authorization_header(user: User) -> dict[str, str]:
    """Return a Bearer header for a persisted test account."""

    return {"Authorization": f"Bearer {create_access_token(user)}"}


def future_slot(hour: int = 10, minute: int = 0) -> tuple[datetime, datetime]:
    """Return a valid clinic-local slot at least two days in the future."""

    clinic_timezone = ZoneInfo("Africa/Nairobi")
    slot_date = datetime.now(clinic_timezone).date() + timedelta(days=2)
    start_time = datetime.combine(slot_date, time(hour, minute), tzinfo=clinic_timezone)
    return start_time.astimezone(UTC), (start_time + timedelta(minutes=30)).astimezone(UTC)


def appointment_payload(doctor_id: int, patient_id: int, start_time: datetime, end_time: datetime) -> dict[str, object]:
    """Build an appointment request body using ISO 8601 timestamps."""

    return {
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
    }
