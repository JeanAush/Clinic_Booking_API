"""Tests for PATCH /appointments/{id}/reschedule."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.models.doctor import Doctor
from app.models.patient import Patient
from tests.conftest import appointment_payload, future_slot


CLINIC_TIMEZONE = ZoneInfo("Africa/Nairobi")


def create_booking(
    client: TestClient,
    doctor: Doctor,
    patient: Patient,
    hour: int = 10,
    minute: int = 0,
) -> tuple[int, datetime, datetime]:
    """Create a future booking and return its ID and time range."""

    start_time, end_time = future_slot(hour=hour, minute=minute)
    response = client.post("/appointments", json=appointment_payload(doctor.id, patient.id, start_time, end_time))
    assert response.status_code == 201
    return response.json()["id"], start_time, end_time


def reschedule_payload(start_time: datetime, end_time: datetime) -> dict[str, str]:
    """Build a reschedule request body from timezone-aware timestamps."""

    return {"start_time": start_time.isoformat(), "end_time": end_time.isoformat()}


def test_reschedule_succeeds_and_preserves_booked_status(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """A valid appointment moves to its requested slot without a new record."""

    appointment_id, _, _ = create_booking(client, doctor, patient)
    new_start, new_end = future_slot(hour=10, minute=30)

    response = client.patch(
        f"/appointments/{appointment_id}/reschedule", json=reschedule_payload(new_start, new_end)
    )

    assert response.status_code == 200
    assert response.json()["id"] == appointment_id
    assert response.json()["status"] == "BOOKED"
    returned_start = datetime.fromisoformat(response.json()["start_time"])
    returned_end = datetime.fromisoformat(response.json()["end_time"])
    assert returned_start == new_start
    assert returned_end == new_end
    assert response.json()["start_time"] == new_start.astimezone(CLINIC_TIMEZONE).isoformat()
    assert response.json()["end_time"] == new_end.astimezone(CLINIC_TIMEZONE).isoformat()


def test_rescheduling_to_occupied_slot_conflicts(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """Existing active bookings still prevent double-booking during rescheduling."""

    appointment_id, _, _ = create_booking(client, doctor, patient, hour=10)
    _, occupied_start, occupied_end = create_booking(client, doctor, patient, hour=11)

    response = client.patch(
        f"/appointments/{appointment_id}/reschedule", json=reschedule_payload(occupied_start, occupied_end)
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "This doctor is no longer available for the selected slot."


def test_rescheduling_outside_working_hours_is_rejected(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """The normal working-hours validation applies to replacement slots."""

    appointment_id, _, _ = create_booking(client, doctor, patient)
    start_time, end_time = future_slot(hour=17)

    response = client.patch(
        f"/appointments/{appointment_id}/reschedule", json=reschedule_payload(start_time, end_time)
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Appointment is outside the doctor's working hours."


def test_rescheduling_to_past_slot_is_rejected(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """Past replacement slots are rejected by the shared validation rules."""

    appointment_id, _, _ = create_booking(client, doctor, patient)
    start_time = datetime.now(UTC) - timedelta(minutes=30)
    end_time = start_time + timedelta(minutes=30)

    response = client.patch(
        f"/appointments/{appointment_id}/reschedule", json=reschedule_payload(start_time, end_time)
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Appointment start time must be in the future."


def test_rescheduling_within_one_hour_is_rejected(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """The booking notice requirement also applies when rescheduling."""

    appointment_id, _, _ = create_booking(client, doctor, patient)
    start_time = datetime.now(UTC) + timedelta(minutes=30)
    end_time = start_time + timedelta(minutes=30)

    response = client.patch(
        f"/appointments/{appointment_id}/reschedule", json=reschedule_payload(start_time, end_time)
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Appointments must be booked at least one hour in advance."


def test_rescheduling_to_invalid_half_hour_boundary_is_rejected(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """Replacement slots must start on the same allowed boundaries as bookings."""

    appointment_id, _, _ = create_booking(client, doctor, patient)
    start_time, end_time = future_slot(hour=10, minute=15)

    response = client.patch(
        f"/appointments/{appointment_id}/reschedule", json=reschedule_payload(start_time, end_time)
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Appointment start time must be on a 30-minute boundary."


def test_rescheduling_cancelled_appointment_conflicts(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """Cancelled appointments cannot be made active again by rescheduling."""

    appointment_id, _, _ = create_booking(client, doctor, patient)
    assert client.patch(f"/appointments/{appointment_id}/cancel", json={"reason": "Schedule changed"}).status_code == 200
    new_start, new_end = future_slot(hour=10, minute=30)

    response = client.patch(
        f"/appointments/{appointment_id}/reschedule", json=reschedule_payload(new_start, new_end)
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Cancelled appointments cannot be rescheduled."


def test_rescheduling_releases_original_slot(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """The original slot returns to availability after a successful move."""

    appointment_id, original_start, _ = create_booking(client, doctor, patient)
    new_start, new_end = future_slot(hour=10, minute=30)
    assert client.patch(
        f"/appointments/{appointment_id}/reschedule", json=reschedule_payload(new_start, new_end)
    ).status_code == 200

    appointment_date = original_start.astimezone(CLINIC_TIMEZONE).date()
    availability = client.get(
        f"/doctors/{doctor.id}/availability", params={"date": appointment_date.isoformat()}
    )

    assert original_start.astimezone(CLINIC_TIMEZONE).isoformat() in availability.json()["slots"]


def test_rescheduling_occupies_new_slot(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """The replacement slot is no longer listed as available."""

    appointment_id, original_start, _ = create_booking(client, doctor, patient)
    new_start, new_end = future_slot(hour=10, minute=30)
    assert client.patch(
        f"/appointments/{appointment_id}/reschedule", json=reschedule_payload(new_start, new_end)
    ).status_code == 200

    appointment_date = original_start.astimezone(CLINIC_TIMEZONE).date()
    availability = client.get(
        f"/doctors/{doctor.id}/availability", params={"date": appointment_date.isoformat()}
    )

    assert new_start.astimezone(CLINIC_TIMEZONE).isoformat() not in availability.json()["slots"]


def test_rescheduling_keeps_appointment_id(
    client: TestClient, doctor: Doctor, patient: Patient
) -> None:
    """Rescheduling updates the existing appointment instead of creating another one."""

    appointment_id, _, _ = create_booking(client, doctor, patient)
    new_start, new_end = future_slot(hour=10, minute=30)

    response = client.patch(
        f"/appointments/{appointment_id}/reschedule", json=reschedule_payload(new_start, new_end)
    )

    assert response.status_code == 200
    assert response.json()["id"] == appointment_id


def test_rescheduling_unknown_appointment_returns_not_found(client: TestClient) -> None:
    """Rescheduling requires an existing appointment."""

    start_time, end_time = future_slot(hour=10, minute=30)
    response = client.patch(
        "/appointments/999999/reschedule", json=reschedule_payload(start_time, end_time)
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Appointment not found."
