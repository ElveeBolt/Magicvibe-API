import structlog
from fastapi import FastAPI, status
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse

from .core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    GoneError,
    NotFoundError,
)

logger = structlog.get_logger(__name__)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request, exc):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(request, exc):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    @app.exception_handler(BadRequestError)
    async def bad_request_handler(request, exc):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request, exc: ForbiddenError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc), **exc.details},
        )

    @app.exception_handler(GoneError)
    async def gone_handler(request, exc):
        return JSONResponse(
            status_code=status.HTTP_410_GONE,
            content={"detail": str(exc)},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_handler(request, exc):
        logger.warning("integrity_error", error=str(exc.orig))
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Conflict"},
        )
