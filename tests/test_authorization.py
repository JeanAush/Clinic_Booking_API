"""Role and ownership authorization tests."""

from datetime import UTC, datetime, time, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User, UserRole
from tests.conftest import appointment_payload, authorization_header, future_slot


def test_patient_cannot_access_admin_management(client: TestClient, patient_user: User) -> None:
    """Patient accounts cannot access doctor management resources."""

    response = client.get("/doctors", headers=authorization_header(patient_user))

    assert response.status_code == 403


def test_patient_can_only_read_their_own_appointments(
    client: TestClient,
    session: Session,
    patient: Patient,
    patient_user: User,
) -> None:
    """Changing a patient ID in the URL cannot disclose another patient's appointments."""

    other_patient = Patient(name="Other Patient", email=f"other-{uuid4().hex}@example.test")
    session.add(other_patient)
    session.flush()

    own = client.get(f"/patients/{patient.id}/appointments", headers=authorization_header(patient_user))
    other = client.get(
        f"/patients/{other_patient.id}/appointments", headers=authorization_header(patient_user)
    )

    assert own.status_code == 200
    assert other.status_code == 403


def test_patient_cannot_book_for_another_patient(
    client: TestClient,
    session: Session,
    doctor: Doctor,
    patient_user: User,
) -> None:
    """A patient cannot impersonate another profile in a booking request body."""

    other_patient = Patient(name="Other Patient", email=f"other-{uuid4().hex}@example.test")
    session.add(other_patient)
    session.flush()
    start_time, end_time = future_slot()

    response = client.post(
        "/appointments",
        json=appointment_payload(doctor.id, other_patient.id, start_time, end_time),
        headers=authorization_header(patient_user),
    )

    assert response.status_code == 403


def test_doctor_can_manage_only_their_own_appointments(
    client: TestClient,
    session: Session,
    doctor: Doctor,
    doctor_user: User,
    patient: Patient,
) -> None:
    """Doctors may cancel appointments assigned to them, but not another doctor."""

    start_time, end_time = future_slot()
    own_appointment = Appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        start_time=start_time,
        end_time=end_time,
        status=AppointmentStatus.BOOKED,
    )
    other_doctor = Doctor(
        name="Other Doctor",
        email=f"other-doctor-{uuid4().hex}@example.test",
        working_start=time(8),
        working_end=time(17),
    )
    session.add_all([own_appointment, other_doctor])
    session.flush()
    other_appointment = Appointment(
        doctor_id=other_doctor.id,
        patient_id=patient.id,
        start_time=start_time + timedelta(hours=1),
        end_time=end_time + timedelta(hours=1),
        status=AppointmentStatus.BOOKED,
    )
    session.add(other_appointment)
    session.flush()

    own = client.patch(
        f"/appointments/{own_appointment.id}/cancel",
        json={"reason": "Doctor unavailable"},
        headers=authorization_header(doctor_user),
    )
    other = client.patch(
        f"/appointments/{other_appointment.id}/cancel",
        json={"reason": "Not allowed"},
        headers=authorization_header(doctor_user),
    )

    assert own.status_code == 200
    assert other.status_code == 403
