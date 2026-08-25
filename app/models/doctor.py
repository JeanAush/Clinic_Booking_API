"""Doctor database model."""

from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.user import User


class Doctor(Base):
    """A clinician with a defined daily working window."""

    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    working_start: Mapped[time] = mapped_column(Time, nullable=False)
    working_end: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")
    user: Mapped["User | None"] = relationship(back_populates="doctor")
