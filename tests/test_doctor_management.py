"""Tests for doctor management endpoints."""

from fastapi.testclient import TestClient

from app.models.doctor import Doctor


def doctor_payload(**overrides: object) -> dict[str, object]:
    """Build a valid doctor creation payload."""

    payload: dict[str, object] = {
        "name": "Dr. New Doctor",
        "email": "new.doctor@example.test",
        "working_start": "08:00:00",
        "working_end": "16:00:00",
    }
    payload.update(overrides)
    return payload


def test_create_doctor(client: TestClient) -> None:
    """A valid doctor is created and returned."""

    response = client.post("/doctors", json=doctor_payload())

    assert response.status_code == 201
    assert response.json()["id"] > 0
    assert response.json()["name"] == "Dr. New Doctor"
    assert response.json()["email"] == "new.doctor@example.test"
    assert response.json()["working_start"] == "08:00:00"
    assert response.json()["working_end"] == "16:00:00"
    assert response.json()["created_at"]


def test_get_doctor(client: TestClient, doctor: Doctor) -> None:
    """A known doctor can be retrieved."""

    response = client.get(f"/doctors/{doctor.id}")

    assert response.status_code == 200
    assert response.json()["id"] == doctor.id
    assert response.json()["email"] == doctor.email


def test_list_doctors(client: TestClient, doctor: Doctor) -> None:
    """The doctor listing includes registered doctors."""

    created = client.post("/doctors", json=doctor_payload(email="listed.doctor@example.test"))
    response = client.get("/doctors")

    assert created.status_code == 201
    assert [item["id"] for item in response.json()] == sorted(item["id"] for item in response.json())
    assert {item["id"] for item in response.json()} >= {doctor.id, created.json()["id"]}


def test_create_doctor_rejects_invalid_input(client: TestClient) -> None:
    """Blank names, invalid emails, and invalid working hours are rejected."""

    for payload in (
        {"email": "missing.name@example.test", "working_start": "08:00:00", "working_end": "16:00:00"},
        doctor_payload(name="   "),
        doctor_payload(email="not-an-email"),
        doctor_payload(working_start="16:00:00", working_end="08:00:00"),
    ):
        assert client.post("/doctors", json=payload).status_code == 422


def test_unknown_doctor_returns_not_found(client: TestClient) -> None:
    """Retrieving an unknown doctor returns 404."""

    response = client.get("/doctors/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Doctor not found."


def test_duplicate_doctor_email_returns_conflict(client: TestClient) -> None:
    """The existing unique email constraint returns a conflict response."""

    assert client.post("/doctors", json=doctor_payload()).status_code == 201
    response = client.post("/doctors", json=doctor_payload())

    assert response.status_code == 409
    assert response.json()["detail"] == "A doctor with this email already exists."
