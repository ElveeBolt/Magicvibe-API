import pytest

from magicvibe.core.exceptions import (
    ERROR_STATUSES,
    BadRequestError,
    ConflictError,
    ErrorCode,
    ForbiddenError,
    NotFoundError,
    ServiceError,
    UnauthorizedError,
)

# The code table of docs/architecture/errors.md, written out on purpose: a
# change to a status must be a change to the document first.
DOCUMENTED_STATUSES = {
    "INVALID_SERVICE_TOKEN": 401,
    "VALIDATION_ERROR": 400,
    "BAD_REQUEST": 400,
    "NOT_FOUND": 404,
    "METHOD_NOT_ALLOWED": 405,
    "CONFLICT": 409,
    "INTERNAL_ERROR": 500,
    "USER_NOT_FOUND": 404,
    "USER_BANNED": 403,
    "PROFILE_REQUIRED": 409,
    "PREFERENCES_REQUIRED": 409,
    "PHOTO_LIMIT_REACHED": 409,
    "SELF_ACTION": 400,
    "ALREADY_REACTED": 409,
    "DAILY_LIMIT_REACHED": 429,
    "PREMIUM_REQUIRED": 403,
    "PREMIUM_ALREADY_ACTIVE": 409,
    "TARGET_USER_BANNED": 409,
    "BAN_ALREADY_ACTIVE": 409,
}


def test_codes_match_the_documented_table() -> None:
    assert {code.value for code in ErrorCode} == set(DOCUMENTED_STATUSES)


def test_every_code_has_its_documented_status() -> None:
    assert {code.value: status for code, status in ERROR_STATUSES.items()} == (
        DOCUMENTED_STATUSES
    )


@pytest.mark.parametrize(
    ("error_cls", "code"),
    [
        (NotFoundError, ErrorCode.NOT_FOUND),
        (ConflictError, ErrorCode.CONFLICT),
        (BadRequestError, ErrorCode.BAD_REQUEST),
        (UnauthorizedError, ErrorCode.INVALID_SERVICE_TOKEN),
    ],
)
def test_error_class_default_code(
    error_cls: type[ServiceError], code: ErrorCode
) -> None:
    error = error_cls()

    assert error.code is code
    assert error.status_code == ERROR_STATUSES[code]


def test_status_follows_the_code_not_the_class() -> None:
    error = ConflictError("Already reacted", code=ErrorCode.ALREADY_REACTED)

    assert error.status_code == 409
    assert error.code is ErrorCode.ALREADY_REACTED


def test_forbidden_error_needs_a_code() -> None:
    with pytest.raises(TypeError):
        ForbiddenError("No code")

    assert ForbiddenError(code=ErrorCode.USER_BANNED).status_code == 403


def test_extra_and_headers_are_kept() -> None:
    error = ForbiddenError(
        code=ErrorCode.USER_BANNED,
        extra={"ban": {"reason": "spam", "comment": None}},
        headers={"X-Test": "1"},
    )

    assert error.extra == {"ban": {"reason": "spam", "comment": None}}
    assert error.headers == {"X-Test": "1"}
