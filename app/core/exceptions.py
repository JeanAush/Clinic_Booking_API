"""Domain errors and their HTTP response translation."""

from fastapi import Request
from fastapi.responses import JSONResponse


class ServiceError(Exception):
    """Base error containing a safe HTTP response description."""

    status_code = 400

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(ServiceError):
    """Raised when a requested database record does not exist."""

    status_code = 404


class ValidationError(ServiceError):
    """Raised when a request breaks an appointment booking rule."""

    status_code = 422


class ConflictError(ServiceError):
    """Raised when a valid request conflicts with existing state."""

    status_code = 409


class AuthenticationError(ServiceError):
    """Raised when credentials or an access token cannot be authenticated."""

    status_code = 401


class ForbiddenError(ServiceError):
    """Raised when an authenticated account lacks permission for an action."""

    status_code = 403


async def service_error_response(_: Request, error: ServiceError) -> JSONResponse:
    """Convert a domain error to the established API error response shape."""

    return JSONResponse(status_code=error.status_code, content={"detail": error.detail})
