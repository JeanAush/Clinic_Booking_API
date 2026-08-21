"""Tests for POST /appointments."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.doctor import Doctor
from app.models.patient import Patient
from tests.conftest import appointment_payload, future_slot


def test_book_appointment_successfully(client: TestClient, doctor: Doctor, patient: Patient) -> None:
    """A valid booking is created and returned."""

    start_time, end_time = future_slot()
    response = client.post("/appointments", json=appointment_payload(doctor.id, patient.id, start_time, end_time))

    assert response.status_code == 201
    assert response.json()["status"] == "BOOKED"
    assert response.json()["doctor_id"] == doctor.id


def test_booking_rejects_nonexistent_doctor(client: TestClient, patient: Patient) -> None:
    """Bookings require an existing doctor."""

    start_time, end_time = future_slot()
    response = client.post("/appointments", json=appointment_payload(999_999, patient.id, start_time, end_time))

    assert response.status_code == 404
    assert response.json()["detail"] == "Doctor not found."


def test_booking_rejects_nonexistent_patient(client: TestClient, doctor: Doctor) -> None:
    """Bookings require an existing patient."""

    start_time, end_time = future_slot()
    response = client.post("/appointments", json=appointment_payload(doctor.id, 999_999, start_time, end_time))

    assert response.status_code == 404
    assert response.json()["detail"] == "Patient not found."


def test_booking_rejects_past_appointment(client: TestClient, doctor: Doctor, patient: Patient) -> None:
    """Appointments cannot start in the past."""

    start_time = datetime.now(UTC) - timedelta(minutes=30)
    end_time = start_time + timedelta(minutes=30)
    response = client.post("/appointments", json=appointment_payload(doctor.id, patient.id, start_time, end_time))

    assert response.status_code == 422
    assert response.json()["detail"] == "Appointment start time must be in the future."


def test_booking_rejects_slot_within_one_hour(client: TestClient, doctor: Doctor, patient: Patient) -> None:
    """Appointments must meet the minimum booking notice."""

    start_time = datetime.now(UTC) + timedelta(minutes=30)
    end_time = start_time + timedelta(minutes=30)
    response = client.post("/appointments", json=appointment_payload(doctor.id, patient.id, start_time, end_time))

    assert response.status_code == 422
    assert response.json()["detail"] == "Appointments must be booked at least one hour in advance."


def test_booking_rejects_invalid_half_hour_boundary(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """The start time must align with a 30-minute slot."""

    start_time, end_time = future_slot(minute=15)
    response = client.post("/appointments", json=appointment_payload(doctor.id, patient.id, start_time, end_time))

    assert response.status_code == 422
    assert response.json()["detail"] == "Appointment start time must be on a 30-minute boundary."


def test_booking_rejects_invalid_duration(client: TestClient, doctor: Doctor, patient: Patient) -> None:
    """Appointments must occupy exactly one 30-minute slot."""

    start_time, end_time = future_slot()
    response = client.post(
        "/appointments",
        json=appointment_payload(doctor.id, patient.id, start_time, end_time + timedelta(minutes=30)),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Appointment duration must be exactly 30 minutes."


def test_booking_rejects_slot_outside_working_hours(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """The full 30-minute appointment must be within the doctor's day."""

    start_time, end_time = future_slot(hour=17)
    response = client.post("/appointments", json=appointment_payload(doctor.id, patient.id, start_time, end_time))

    assert response.status_code == 422
    assert response.json()["detail"] == "Appointment is outside the doctor's working hours."


def test_booking_rejects_double_booking(client: TestClient, doctor: Doctor, patient: Patient) -> None:
    """The database exclusion constraint prevents the same slot being booked twice."""

    start_time, end_time = future_slot()
    payload = appointment_payload(doctor.id, patient.id, start_time, end_time)

    assert client.post("/appointments", json=payload).status_code == 201
    response = client.post("/appointments", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "This doctor is no longer available for the selected slot."


def test_booking_accepts_valid_nairobi_timezone_appointment(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """A valid appointment with Africa/Nairobi timezone more than one hour in advance is accepted."""

    from datetime import time
    from zoneinfo import ZoneInfo

    clinic_timezone = ZoneInfo("Africa/Nairobi")
    # Use an explicit +03:00 payload for a future 13:00 Nairobi slot. Keeping
    # the date in the future makes this independent of the test execution time.
    slot_date = datetime.now(clinic_timezone).date() + timedelta(days=2)
    start_time = datetime.combine(slot_date, time(13, 0), tzinfo=clinic_timezone)
    end_time = start_time + timedelta(minutes=30)

    response = client.post("/appointments", json=appointment_payload(doctor.id, patient.id, start_time, end_time))

    assert response.status_code == 201
    assert response.json()["status"] == "BOOKED"
