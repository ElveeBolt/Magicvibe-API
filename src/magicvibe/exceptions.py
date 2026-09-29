from typing import TYPE_CHECKING, Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from .core.exceptions import ERROR_STATUSES, ErrorCode, ServiceError

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = structlog.get_logger(__name__)

# Request parts FastAPI puts first in a validation error's `loc`; the bot needs
# only the path inside the part.
REQUEST_PARTS = frozenset({"body", "query", "path", "header", "cookie"})

# Constraints whose violation has a code of its own. The names are the ones the
# naming convention gives them (see docs/architecture/models.md).
CONSTRAINT_CODES: dict[str, ErrorCode] = {
    "uq_reaction_pair": ErrorCode.ALREADY_REACTED,
    "ix_bans_user_id": ErrorCode.BAN_ALREADY_ACTIVE,
}

HTTP_STATUS_CODES: dict[int, ErrorCode] = {
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
}


def error_response(
    code: ErrorCode,
    detail: str,
    *,
    status_code: int | None = None,
    headers: Mapping[str, str] | None = None,
    **extra: Any,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code or ERROR_STATUSES[code],
        content={"code": code, "detail": detail, **extra},
        headers=headers,
    )


def validation_error_field(loc: tuple[int | str, ...]) -> str:
    if loc and loc[0] in REQUEST_PARTS:
        loc = loc[1:]
    return ".".join(str(part) for part in loc)


def constraint_name(exc: IntegrityError) -> str | None:
    """Name of the violated constraint, read from the asyncpg error that
    SQLAlchemy wraps; `None` when the driver does not report one."""
    for source in (getattr(exc.orig, "__cause__", None), exc.orig):
        name = getattr(source, "constraint_name", None)
        if isinstance(name, str):
            return name
    return None


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ServiceError)
    async def service_error_handler(
        request: Request, exc: ServiceError
    ) -> JSONResponse:
        return error_response(
            exc.code,
            exc.detail,
            status_code=exc.status_code,
            headers=exc.headers,
            **exc.extra,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {
                "field": validation_error_field(tuple(error["loc"])),
                "type": error["type"],
                "message": error["msg"],
            }
            for error in exc.errors()
        ]
        return error_response(
            ErrorCode.VALIDATION_ERROR, "Request validation failed", errors=errors
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = HTTP_STATUS_CODES.get(exc.status_code)

        if code is None:
            code = (
                ErrorCode.INTERNAL_ERROR
                if exc.status_code >= 500
                else ErrorCode.BAD_REQUEST
            )

        return error_response(
            code, str(exc.detail), status_code=exc.status_code, headers=exc.headers
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(
        request: Request, exc: IntegrityError
    ) -> JSONResponse:
        name = constraint_name(exc)
        logger.warning("integrity_error", constraint=name, error=str(exc.orig))
        code = CONSTRAINT_CODES.get(name or "", ErrorCode.CONFLICT)
        return error_response(code, "The request conflicts with the current state")

    # Starlette calls this from ServerErrorMiddleware, outside LoggingMiddleware,
    # and only when `debug` is off (with debug it renders a traceback page).
    @app.exception_handler(Exception)
    async def unexpected_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("unexpected_error", request_id=request_id)
        return error_response(
            ErrorCode.INTERNAL_ERROR, "Internal server error", request_id=request_id
        )
