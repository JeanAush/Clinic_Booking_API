"""Tests for GET /patients/{id}/appointments."""

from datetime import UTC, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.patient import Patient


def create_appointment(
    session: Session,
    doctor: Doctor,
    patient: Patient,
    start_time: datetime,
) -> Appointment:
    """Persist an appointment for retrieval tests."""

    appointment = Appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        start_time=start_time,
        end_time=start_time + timedelta(minutes=30),
        status=AppointmentStatus.BOOKED,
    )
    session.add(appointment)
    session.flush()
    return appointment


def test_patient_upcoming_appointments_are_returned(
    client: TestClient, session: Session, doctor: Doctor, patient: Patient
) -> None:
    """The endpoint returns appointment details for a patient's future booking."""

    appointment = create_appointment(session, doctor, patient, datetime.now(UTC) + timedelta(days=2))

    response = client.get(f"/patients/{patient.id}/appointments")

    assert response.status_code == 200
    assert len(response.json()) == 1
    returned_appointment = response.json()[0]
    assert returned_appointment["id"] == appointment.id
    assert returned_appointment["doctor_id"] == doctor.id
    assert returned_appointment["patient_id"] == patient.id
    assert returned_appointment["status"] == "BOOKED"


def test_patient_appointments_are_sorted_chronologically(
    client: TestClient, session: Session, doctor: Doctor, patient: Patient
) -> None:
    """Appointments are returned in ascending start-time order."""

    later = create_appointment(session, doctor, patient, datetime.now(UTC) + timedelta(days=3))
    earlier = create_appointment(session, doctor, patient, datetime.now(UTC) + timedelta(days=2))

    response = client.get(f"/patients/{patient.id}/appointments")

    assert response.status_code == 200
    assert [appointment["id"] for appointment in response.json()] == [earlier.id, later.id]


def test_past_patient_appointments_are_excluded(
    client: TestClient, session: Session, doctor: Doctor, patient: Patient
) -> None:
    """Appointments with starts before the current clinic time are omitted."""

    past = create_appointment(session, doctor, patient, datetime.now(UTC) - timedelta(days=1))
    upcoming = create_appointment(session, doctor, patient, datetime.now(UTC) + timedelta(days=2))

    response = client.get(f"/patients/{patient.id}/appointments")

    assert response.status_code == 200
    assert [appointment["id"] for appointment in response.json()] == [upcoming.id]
    assert past.id not in [appointment["id"] for appointment in response.json()]


def test_patient_without_upcoming_appointments_returns_empty_list(
    client: TestClient, patient: Patient
) -> None:
    """Patients with no future bookings receive an empty result."""

    response = client.get(f"/patients/{patient.id}/appointments")

    assert response.status_code == 200
    assert response.json() == []


def test_unknown_patient_appointments_returns_not_found(client: TestClient) -> None:
    """The endpoint requires an existing patient."""

    response = client.get("/patients/999999/appointments")

    assert response.status_code == 404
    assert response.json()["detail"] == "Patient not found."
