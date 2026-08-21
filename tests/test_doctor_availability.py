"""Tests for GET /doctors/{id}/availability."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.services.availability import get_doctor_availability


CLINIC_TIMEZONE = ZoneInfo("Africa/Nairobi")


def local_slot(appointment_date: date, hour: int, minute: int = 0) -> tuple[datetime, datetime]:
    """Build a 30-minute appointment range in the clinic timezone."""

    start_time = datetime.combine(appointment_date, time(hour, minute), tzinfo=CLINIC_TIMEZONE)
    return start_time, start_time + timedelta(minutes=30)


def create_appointment(
    session: Session,
    doctor: Doctor,
    patient: Patient,
    start_time: datetime,
    end_time: datetime,
    status: AppointmentStatus,
) -> None:
    """Persist an appointment that may or may not occupy an availability slot."""

    session.add(
        Appointment(
            doctor_id=doctor.id,
            patient_id=patient.id,
            start_time=start_time.astimezone(UTC),
            end_time=end_time.astimezone(UTC),
            status=status,
        )
    )
    session.flush()


def test_availability_returns_slots_within_working_hours(
    client: TestClient, doctor: Doctor
) -> None:
    """Availability contains every 30-minute start that fits the working day."""

    appointment_date = datetime.now(CLINIC_TIMEZONE).date() + timedelta(days=2)
    response = client.get(f"/doctors/{doctor.id}/availability", params={"date": appointment_date.isoformat()})

    assert response.status_code == 200
    body = response.json()
    assert body["doctor_id"] == doctor.id
    assert body["date"] == appointment_date.isoformat()
    assert body["slots"] == [
        datetime.combine(appointment_date, time(hour, minute), tzinfo=CLINIC_TIMEZONE).isoformat()
        for hour in range(8, 17)
        for minute in (0, 30)
    ]


def test_availability_excludes_booked_slots(
    client: TestClient, session: Session, doctor: Doctor, patient: Patient
) -> None:
    """An active booking makes its slot unavailable."""

    appointment_date = datetime.now(CLINIC_TIMEZONE).date() + timedelta(days=2)
    start_time, end_time = local_slot(appointment_date, 10)
    create_appointment(session, doctor, patient, start_time, end_time, AppointmentStatus.BOOKED)

    response = client.get(f"/doctors/{doctor.id}/availability", params={"date": appointment_date.isoformat()})

    assert response.status_code == 200
    assert start_time.isoformat() not in response.json()["slots"]
    assert len(response.json()["slots"]) == 17


def test_cancelled_appointment_does_not_block_availability(
    client: TestClient, session: Session, doctor: Doctor, patient: Patient
) -> None:
    """Cancelled appointments are ignored when calculating availability."""

    appointment_date = datetime.now(CLINIC_TIMEZONE).date() + timedelta(days=2)
    start_time, end_time = local_slot(appointment_date, 10)
    create_appointment(session, doctor, patient, start_time, end_time, AppointmentStatus.CANCELLED)

    response = client.get(f"/doctors/{doctor.id}/availability", params={"date": appointment_date.isoformat()})

    assert response.status_code == 200
    assert start_time.isoformat() in response.json()["slots"]


def test_today_availability_requires_one_hour_notice(session: Session, doctor: Doctor) -> None:
    """Today's slots before the booking-notice cutoff are hidden."""

    now = datetime(2026, 8, 24, 9, 15, tzinfo=CLINIC_TIMEZONE)
    slots = get_doctor_availability(session, doctor.id, now.date(), "Africa/Nairobi", now=now)

    assert [slot.time() for slot in slots] == [
        time(10, 30),
        time(11, 0),
        time(11, 30),
        time(12, 0),
        time(12, 30),
        time(13, 0),
        time(13, 30),
        time(14, 0),
        time(14, 30),
        time(15, 0),
        time(15, 30),
        time(16, 0),
        time(16, 30),
    ]


def test_past_slots_are_excluded(session: Session, doctor: Doctor) -> None:
    """Slots before the current clinic-local time are never returned."""

    now = datetime(2026, 8, 24, 16, 45, tzinfo=CLINIC_TIMEZONE)
    slots = get_doctor_availability(session, doctor.id, now.date(), "Africa/Nairobi", now=now)

    assert slots == []


def test_availability_returns_not_found_for_unknown_doctor(client: TestClient) -> None:
    """Availability requests require an existing doctor."""

    response = client.get("/doctors/999999/availability", params={"date": "2026-08-24"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Doctor not found."


def test_availability_is_registered_in_openapi() -> None:
    """The availability endpoint is visible through FastAPI Swagger/OpenAPI."""

    from app.main import app

    operation = app.openapi()["paths"]["/doctors/{doctor_id}/availability"]["get"]

    assert operation["operationId"]
    assert {parameter["name"] for parameter in operation["parameters"]} == {"doctor_id", "date"}
