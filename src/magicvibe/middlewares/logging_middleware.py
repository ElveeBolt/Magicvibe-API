import time
from typing import TYPE_CHECKING
from uuid import uuid4

import structlog

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = structlog.get_logger(__name__)


class LoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        structlog.contextvars.clear_contextvars()

        headers = dict(scope["headers"])

        request_id = headers.get(b"x-request-id", str(uuid4()).encode()).decode()

        method = scope["method"]
        path = scope["path"]

        structlog.contextvars.bind_contextvars(
            request_id=request_id, method=method, path=path
        )
        # The 500 handler runs outside this middleware and reads it from here.
        scope.setdefault("state", {})["request_id"] = request_id

        started_at = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - started_at) * 1000

            logger.info(
                "request_completed",
                status_code=status_code,
                duration_ms=round(duration_ms, 2),
            )
