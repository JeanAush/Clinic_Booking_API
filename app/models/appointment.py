"""Appointment database model and booking status."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.doctor import Doctor
    from app.models.patient import Patient


class AppointmentStatus(str, Enum):
    """States an appointment can occupy."""

    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"


class Appointment(Base):
    """A 30-minute appointment between a doctor and patient."""

    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_appointments_end_after_start"),
        CheckConstraint(
            "end_time = start_time + INTERVAL '30 minutes'",
            name="ck_appointments_thirty_minute_duration",
        ),
        ExcludeConstraint(
            ("doctor_id", "="),
            (text("tstzrange(start_time, end_time, '[)')"), "&&"),
            where=text("status = 'BOOKED'"),
            name="ex_appointments_active_doctor_time",
            using="gist",
        ),
        Index("ix_appointments_doctor_start_time", "doctor_id", "start_time"),
        Index("ix_appointments_patient_start_time", "patient_id", "start_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        SqlEnum(AppointmentStatus, name="appointment_status"),
        default=AppointmentStatus.BOOKED,
        server_default=AppointmentStatus.BOOKED.value,
        nullable=False,
    )
    cancellation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    doctor: Mapped["Doctor"] = relationship(back_populates="appointments")
    patient: Mapped["Patient"] = relationship(back_populates="appointments")
