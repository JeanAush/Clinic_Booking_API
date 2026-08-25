"""Database queries for appointment records."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus


class AppointmentRepository:
    """Organize appointment persistence and query operations for a session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, appointment_id: int) -> Appointment | None:
        """Return an appointment by primary key when it exists."""

        return self._session.get(Appointment, appointment_id)

    def add(self, appointment: Appointment) -> None:
        """Stage a new appointment for the current transaction."""

        self._session.add(appointment)

    def list_active_for_doctor_between(
        self,
        doctor_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> list[Appointment]:
        """Return booked appointments overlapping the supplied UTC time window."""

        return list(
            self._session.scalars(
                select(Appointment).where(
                    Appointment.doctor_id == doctor_id,
                    Appointment.status == AppointmentStatus.BOOKED,
                    Appointment.start_time < end_time.astimezone(UTC),
                    Appointment.end_time > start_time.astimezone(UTC),
                )
            )
        )

    def list_upcoming_for_patient(self, patient_id: int, current_time: datetime) -> list[Appointment]:
        """Return a patient's upcoming appointments in chronological order."""

        return list(
            self._session.scalars(
                select(Appointment)
                .where(
                    Appointment.patient_id == patient_id,
                    Appointment.start_time > current_time.astimezone(UTC),
                )
                .order_by(Appointment.start_time.asc())
            )
        )
