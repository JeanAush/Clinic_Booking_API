"""Authentication account database model."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.doctor import Doctor
    from app.models.patient import Patient


class UserRole(str, Enum):
    """Roles recognized by the clinic authorization policy."""

    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"


class User(Base):
    """Login account optionally associated with one clinic profile."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "(role = 'ADMIN' AND doctor_id IS NULL AND patient_id IS NULL) OR "
            "(role = 'DOCTOR' AND doctor_id IS NOT NULL AND patient_id IS NULL) OR "
            "(role = 'PATIENT' AND patient_id IS NOT NULL AND doctor_id IS NULL)",
            name="ck_users_role_profile",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole, name="user_role"), nullable=False)
    doctor_id: Mapped[int | None] = mapped_column(ForeignKey("doctors.id"), unique=True, nullable=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    doctor: Mapped["Doctor | None"] = relationship(back_populates="user")
    patient: Mapped["Patient | None"] = relationship(back_populates="user")
