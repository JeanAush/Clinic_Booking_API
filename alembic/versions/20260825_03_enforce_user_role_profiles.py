"""Enforce the role-to-profile account invariant.

Revision ID: 20260825_03
Revises: 20260825_02
Create Date: 2026-08-25
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260825_03"
down_revision: str | None = "20260825_02"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

CONSTRAINT_NAME = "ck_users_role_profile"
CONSTRAINT_SQL = (
    "(role = 'ADMIN' AND doctor_id IS NULL AND patient_id IS NULL) OR "
    "(role = 'DOCTOR' AND doctor_id IS NOT NULL AND patient_id IS NULL) OR "
    "(role = 'PATIENT' AND patient_id IS NOT NULL AND doctor_id IS NULL)"
)


def upgrade() -> None:
    """Prevent accounts from having role/profile combinations that cannot be authorized safely."""

    op.create_check_constraint(CONSTRAINT_NAME, "users", CONSTRAINT_SQL)


def downgrade() -> None:
    """Remove the role-to-profile database safeguard."""

    op.drop_constraint(CONSTRAINT_NAME, "users", type_="check")
