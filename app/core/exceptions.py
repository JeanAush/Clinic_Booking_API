"""Domain errors returned by application services."""


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
