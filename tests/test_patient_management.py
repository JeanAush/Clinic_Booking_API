"""Tests for patient management endpoints."""

from fastapi.testclient import TestClient

from app.models.patient import Patient


def patient_payload(**overrides: object) -> dict[str, object]:
    """Build a valid patient creation payload."""

    payload: dict[str, object] = {"name": "New Patient", "email": "new.patient@example.test"}
    payload.update(overrides)
    return payload


def test_create_patient(client: TestClient) -> None:
    """A valid patient is created and returned."""

    response = client.post("/patients", json=patient_payload())

    assert response.status_code == 201
    assert response.json()["name"] == "New Patient"
    assert response.json()["email"] == "new.patient@example.test"
    assert response.json()["id"] > 0
    assert response.json()["created_at"]


def test_get_patient(client: TestClient, patient: Patient) -> None:
    """A known patient can be retrieved."""

    response = client.get(f"/patients/{patient.id}")

    assert response.status_code == 200
    assert response.json()["id"] == patient.id
    assert response.json()["email"] == patient.email


def test_list_patients(client: TestClient, patient: Patient) -> None:
    """The patient listing includes registered patients."""

    created = client.post("/patients", json=patient_payload(email="listed.patient@example.test"))
    response = client.get("/patients")

    assert created.status_code == 201
    assert [item["id"] for item in response.json()] == sorted(item["id"] for item in response.json())
    assert {item["id"] for item in response.json()} >= {patient.id, created.json()["id"]}


def test_create_patient_rejects_invalid_input(client: TestClient) -> None:
    """Blank names and invalid emails are rejected."""

    for payload in (
        {"email": "missing.name@example.test"},
        patient_payload(name="   "),
        patient_payload(email="not-an-email"),
    ):
        assert client.post("/patients", json=payload).status_code == 422


def test_unknown_patient_returns_not_found(client: TestClient) -> None:
    """Retrieving an unknown patient returns 404."""

    response = client.get("/patients/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Patient not found."


def test_duplicate_patient_email_returns_conflict(client: TestClient) -> None:
    """The existing unique email constraint returns a conflict response."""

    assert client.post("/patients", json=patient_payload()).status_code == 201
    response = client.post("/patients", json=patient_payload())

    assert response.status_code == 409
    assert response.json()["detail"] == "A patient with this email already exists."
