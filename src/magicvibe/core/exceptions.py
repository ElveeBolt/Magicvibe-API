from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    """
    Stable, machine-readable error reasons. The list and the statuses follow
    `docs/architecture/errors.md`.
    """

    # General
    INVALID_SERVICE_TOKEN = "INVALID_SERVICE_TOKEN"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    BAD_REQUEST = "BAD_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    # Accounts
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_BANNED = "USER_BANNED"

    # Profile, discovery and reactions
    PROFILE_REQUIRED = "PROFILE_REQUIRED"
    PREFERENCES_REQUIRED = "PREFERENCES_REQUIRED"
    PHOTO_LIMIT_REACHED = "PHOTO_LIMIT_REACHED"
    SELF_ACTION = "SELF_ACTION"
    ALREADY_REACTED = "ALREADY_REACTED"
    DAILY_LIMIT_REACHED = "DAILY_LIMIT_REACHED"
    PREMIUM_REQUIRED = "PREMIUM_REQUIRED"

    # Administration
    PREMIUM_ALREADY_ACTIVE = "PREMIUM_ALREADY_ACTIVE"
    TARGET_USER_BANNED = "TARGET_USER_BANNED"
    BAN_ALREADY_ACTIVE = "BAN_ALREADY_ACTIVE"


ERROR_STATUSES: dict[ErrorCode, int] = {
    ErrorCode.INVALID_SERVICE_TOKEN: 401,
    ErrorCode.VALIDATION_ERROR: 400,
    ErrorCode.BAD_REQUEST: 400,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.METHOD_NOT_ALLOWED: 405,
    ErrorCode.CONFLICT: 409,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.USER_NOT_FOUND: 404,
    ErrorCode.USER_BANNED: 403,
    ErrorCode.PROFILE_REQUIRED: 409,
    ErrorCode.PREFERENCES_REQUIRED: 409,
    ErrorCode.PHOTO_LIMIT_REACHED: 409,
    ErrorCode.SELF_ACTION: 400,
    ErrorCode.ALREADY_REACTED: 409,
    ErrorCode.DAILY_LIMIT_REACHED: 429,
    ErrorCode.PREMIUM_REQUIRED: 403,
    ErrorCode.PREMIUM_ALREADY_ACTIVE: 409,
    ErrorCode.TARGET_USER_BANNED: 409,
    ErrorCode.BAN_ALREADY_ACTIVE: 409,
}


class ServiceError(Exception):
    """
    Base class for all service-layer exceptions.

    The HTTP status follows from `code` (`ERROR_STATUSES`), so a code can never
    be sent with the wrong status. `extra` is merged into the response body,
    so the client learns what it needs without a second request.
    """

    default_code: ErrorCode | None = None
    default_detail: str = "Error"

    def __init__(
        self,
        detail: str | None = None,
        code: ErrorCode | None = None,
        extra: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ):
        resolved_code = code or self.default_code

        if resolved_code is None:
            raise TypeError(f"{self.__class__.__name__} needs an error code")

        self.code = resolved_code
        self.detail = detail or self.default_detail
        self.extra = extra or {}
        self.headers = headers
        super().__init__(self.detail)

    @property
    def status_code(self) -> int:
        return ERROR_STATUSES[self.code]


class NotFoundError(ServiceError):
    """
    Raised when a requested resource does not exist.
    """

    default_code = ErrorCode.NOT_FOUND
    default_detail = "Resource not found"


class ConflictError(ServiceError):
    """
    Raised when the operation conflicts with the current state of a resource.
    """

    default_code = ErrorCode.CONFLICT
    default_detail = "Conflict"


class BadRequestError(ServiceError):
    """
    Raised when the request is well-formed but violates a business rule.
    """

    default_code = ErrorCode.BAD_REQUEST
    default_detail = "Bad request"


class ForbiddenError(ServiceError):
    """
    Raised when the caller is known but not allowed to perform the action.
    Has no default code: every refusal names its reason.
    """

    default_detail = "Forbidden"


class TooManyRequestsError(ServiceError):
    """
    Raised when a quota of the user is used up (a daily limit).
    """

    default_code = ErrorCode.DAILY_LIMIT_REACHED
    default_detail = "Too many requests"


class UnauthorizedError(ServiceError):
    """
    Raised when the service token is missing or wrong.
    """

    default_code = ErrorCode.INVALID_SERVICE_TOKEN
    default_detail = "Invalid or missing service token"
