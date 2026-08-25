"""Clinic timezone conversion helpers shared by appointment services."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo


def clinic_now(timezone_name: str, now: datetime | None = None) -> datetime:
    """Return the supplied or current time normalized to the clinic timezone."""

    timezone = ZoneInfo(timezone_name)
    return (now or datetime.now(timezone)).astimezone(timezone)


def utc_time(value: datetime) -> datetime:
    """Normalize an aware datetime to UTC."""

    return value.astimezone(UTC)
