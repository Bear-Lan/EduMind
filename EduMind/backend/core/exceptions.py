"""
EduMind Custom Exceptions

All modules must raise these exceptions instead of raw exceptions.
The Learning Orchestrator decides how to handle errors.
"""


class EduMindException(Exception):
    """Base exception for all EduMind errors."""

    def __init__(self, message: str, code: int = 500) -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(EduMindException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code=404,
        )


class ValidationError(EduMindException):
    """Raised when input validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code=400)


class UnauthorizedError(EduMindException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message=message, code=401)


class ServiceUnavailableError(EduMindException):
    """Raised when an external service is not available."""

    def __init__(self, service: str) -> None:
        super().__init__(
            message=f"Service unavailable: {service}",
            code=503,
        )
