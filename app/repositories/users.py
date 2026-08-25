"""Database queries for authentication accounts."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Organize authentication account persistence and lookups."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: int) -> User | None:
        """Return an account by primary key when it exists."""

        return self._session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        """Return an account by normalized login email when it exists."""

        return self._session.scalar(select(User).where(User.email == email.lower()))

    def add(self, user: User) -> None:
        """Stage an account for the current transaction."""

        self._session.add(user)
