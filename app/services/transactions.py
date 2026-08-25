"""Small transaction helpers shared by write-oriented services."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError


def commit_or_raise_conflict(
    session: Session,
    conflict_detail: str,
    constraint_name: str | None = None,
) -> None:
    """Commit a transaction, translating an expected integrity error to a conflict."""

    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        if constraint_name is None or _has_constraint(error, constraint_name):
            raise ConflictError(conflict_detail) from error
        raise


def _has_constraint(error: IntegrityError, constraint_name: str) -> bool:
    """Return whether a PostgreSQL integrity error identifies a constraint."""

    diagnostics = getattr(error.orig, "diag", None)
    return getattr(diagnostics, "constraint_name", None) == constraint_name
