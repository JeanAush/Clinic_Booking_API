"""SQLAlchemy engine and database session management."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def get_database_url() -> str:
    """Return the configured database URL or raise a clear startup error."""

    database_url = get_settings().database_url
    if database_url is None:
        raise RuntimeError("CLINIC_DATABASE_URL must be configured to access the database.")
    return database_url


def create_database_engine() -> Engine:
    """Create the application's PostgreSQL engine."""

    return create_engine(get_database_url(), pool_pre_ping=True)


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a database session and reliably close it afterwards."""

    database_session = SessionLocal()
    try:
        yield database_session
    finally:
        database_session.close()
