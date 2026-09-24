from typing import Any


class ServiceError(Exception):
    """
    Base class for all service-layer exceptions.
    """


class NotFoundError(ServiceError):
    """
    Raised when a requested resource does not exist.
    """

    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(self.message)


class ConflictError(ServiceError):
    """
    Raised when the operation conflicts with the current state of a resource.
    """

    def __init__(self, message: str = "Conflict"):
        self.message = message
        super().__init__(self.message)


class BadRequestError(ServiceError):
    """
    Raised when the request is well-formed but violates a business rule.
    """

    def __init__(self, message: str = "Bad request"):
        self.message = message
        super().__init__(self.message)


class ForbiddenError(ServiceError):
    """
    Raised when the caller is known but not allowed to perform the action.

    `details` is merged into the response body, so the client learns why
    without a second request.
    """

    def __init__(
        self, message: str = "Forbidden", details: dict[str, Any] | None = None
    ):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class GoneError(ServiceError):
    """
    Raised when the resource existed but was deleted.
    """

    def __init__(self, message: str = "Gone"):
        self.message = message
        super().__init__(self.message)
