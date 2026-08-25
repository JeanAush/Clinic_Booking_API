"""Add authentication accounts and role representation.

Revision ID: 20260825_02
Revises: 20260820_01
Create Date: 2026-08-25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260825_02"
down_revision: str | None = "20260820_01"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


user_role = postgresql.ENUM("ADMIN", "DOCTOR", "PATIENT", name="user_role", create_type=False)


def upgrade() -> None:
    """Create login accounts linked one-to-one to clinic profiles."""

    user_role.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=True),
        sa.Column("patient_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("doctor_id"),
        sa.UniqueConstraint("patient_id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)


def downgrade() -> None:
    """Remove authentication accounts and their role type."""

    op.drop_table("users")
    user_role.drop(op.get_bind(), checkfirst=True)
