"""Environment-based application configuration."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Runtime settings loaded from environment variables."""

    app_name: str = Field(default="Clinic Appointment Booking API")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    timezone: str = Field(default="Africa/Nairobi")
    database_url: str | None = Field(default=None)


def _read_env_file() -> dict[str, str]:
    """Read simple KEY=VALUE pairs from an optional local .env file."""

    env_path = Path(".env")
    if not env_path.is_file():
        return {}

    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
            continue
        key, value = stripped_line.split("=", maxsplit=1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""

    file_values = _read_env_file()
    setting_names = ("app_name", "app_env", "debug", "host", "port", "timezone", "database_url")
    environment_values = {}
    for name in setting_names:
        environment_key = f"CLINIC_{name.upper()}"
        if environment_key in file_values:
            environment_values[name] = file_values[environment_key]
        if environment_key in os.environ:
            environment_values[name] = os.environ[environment_key]
    return Settings.model_validate(environment_values)
