from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from .exceptions import register_exception_handlers
from .logging_config import setup_logging
from .metadata import APP_DESCRIPTION, APP_TITLE, APP_VERSION
from .middlewares import LoggingMiddleware
from .router import bot_router
from .settings import settings

setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("App started")

    yield

    logger.info("App stopped")


app = FastAPI(
    debug=settings.debug,
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    redoc_url=None,
)

# Middlewares
app.add_middleware(LoggingMiddleware)

# Routes
app.include_router(bot_router)

# Exceptions
register_exception_handlers(app)
