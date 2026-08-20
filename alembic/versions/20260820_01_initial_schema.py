"""Create the clinic appointment schema.

Revision ID: 20260820_01
Revises:
Create Date: 2026-08-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260820_01"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


appointment_status = postgresql.ENUM(
    "BOOKED",
    "CANCELLED",
    name="appointment_status",
    create_type=False,
)


def upgrade() -> None:
    """Create the initial models, indexes, and booking safeguards."""

    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    appointment_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "doctors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("working_start", sa.Time(), nullable=False),
        sa.Column("working_end", sa.Time(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_doctors_email", "doctors", ["email"], unique=False)

    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_patients_email", "patients", ["email"], unique=False)

    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", appointment_status, server_default="BOOKED", nullable=False),
        sa.Column("cancellation_reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("end_time > start_time", name="ck_appointments_end_after_start"),
        sa.CheckConstraint(
            "end_time = start_time + INTERVAL '30 minutes'",
            name="ck_appointments_thirty_minute_duration",
        ),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
    )
    op.create_index("ix_appointments_doctor_start_time", "appointments", ["doctor_id", "start_time"])
    op.create_index("ix_appointments_patient_start_time", "appointments", ["patient_id", "start_time"])
    op.execute(
        "ALTER TABLE appointments "
        "ADD CONSTRAINT ex_appointments_active_doctor_time "
        "EXCLUDE USING gist (doctor_id WITH =, tstzrange(start_time, end_time, '[)') WITH &&) "
        "WHERE (status = 'BOOKED'::appointment_status)"
    )


def downgrade() -> None:
    """Remove the initial clinic appointment schema."""

    op.drop_table("appointments")
    op.drop_table("patients")
    op.drop_table("doctors")
    appointment_status.drop(op.get_bind(), checkfirst=True)
