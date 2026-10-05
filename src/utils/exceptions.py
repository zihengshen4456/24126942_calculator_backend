"""Business exceptions.

Every predictable failure (invalid expression, division by zero, missing record)
is raised as an exception and converted into a standard JSON response by the
global error handlers, so controllers stay free of error-handling boilerplate.
"""


class AppError(Exception):
    """Base class for business errors."""

    code = "APP_ERROR"
    status = 400

    def __init__(self, message: str, code: str = None, status: int = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status:
            self.status = status


class ValidationError(AppError):
    """Invalid input, mapped to HTTP 400."""

    code = "VALIDATION_ERROR"
    status = 400


class NotFoundError(AppError):
    """Missing resource, mapped to HTTP 404."""

    code = "NOT_FOUND"
    status = 404
