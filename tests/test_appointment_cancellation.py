"""Tests for PATCH /appointments/{id}/cancel."""

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from app.models.doctor import Doctor
from app.models.patient import Patient
from tests.conftest import appointment_payload, future_slot


def create_booking(client: TestClient, doctor: Doctor, patient: Patient) -> tuple[int, datetime]:
    """Create a future booking and return its ID and clinic-local start time."""

    start_time, end_time = future_slot()
    response = client.post("/appointments", json=appointment_payload(doctor.id, patient.id, start_time, end_time))
    assert response.status_code == 201
    return response.json()["id"], start_time


def test_cancellation_marks_appointment_cancelled(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """Cancelling an appointment updates its status."""

    appointment_id, _ = create_booking(client, doctor, patient)
    response = client.patch(f"/appointments/{appointment_id}/cancel", json={"reason": "Schedule changed"})

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_cancellation_stores_reason(client: TestClient, doctor: Doctor, patient: Patient) -> None:
    """The cancellation response includes the recorded reason."""

    appointment_id, _ = create_booking(client, doctor, patient)
    response = client.patch(f"/appointments/{appointment_id}/cancel", json={"reason": "No longer needed"})

    assert response.status_code == 200
    assert response.json()["cancellation_reason"] == "No longer needed"


def test_cancelling_already_cancelled_appointment_conflicts(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """An appointment can only be cancelled once."""

    appointment_id, _ = create_booking(client, doctor, patient)
    assert client.patch(f"/appointments/{appointment_id}/cancel", json={"reason": "First reason"}).status_code == 200

    response = client.patch(f"/appointments/{appointment_id}/cancel", json={"reason": "Second reason"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Appointment is already cancelled."


def test_cancelled_slot_becomes_available(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """Cancelling a booking makes its original slot appear in availability."""

    appointment_id, start_time = create_booking(client, doctor, patient)
    assert client.patch(f"/appointments/{appointment_id}/cancel", json={"reason": "Schedule changed"}).status_code == 200

    clinic_timezone = ZoneInfo("Africa/Nairobi")
    appointment_date = start_time.astimezone(clinic_timezone).date()
    response = client.get(f"/doctors/{doctor.id}/availability", params={"date": appointment_date.isoformat()})

    assert response.status_code == 200
    assert start_time.astimezone(clinic_timezone).isoformat() in response.json()["slots"]


def test_cancelling_unknown_appointment_returns_not_found(client: TestClient) -> None:
    """Cancellation requires an existing appointment."""

    response = client.patch("/appointments/999999/cancel", json={"reason": "Schedule changed"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Appointment not found."
