import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.community.postgres import PostgresContainer

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from fastapi import FastAPI
    from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession

    from magicvibe.uow import UnitOfWork

# Never import `magicvibe` at module level here: its settings, engine and
# Alembic read the environment on import, so it must point to the container
# first (see docs/architecture/testing.md → Settings).

ROOT_DIR = Path(__file__).resolve().parent.parent

# The same image as in docker-compose.yml.
POSTGRES_IMAGE = "postgres:18.6"

SERVICE_TOKEN = "test-service-token"
AUTH_HEADERS = {"Authorization": f"Bearer {SERVICE_TOKEN}"}

_container: PostgresContainer | None = None


def pytest_configure(config: pytest.Config) -> None:
    global _container

    # Fails the session at start when Docker is not running.
    _container = PostgresContainer(
        POSTGRES_IMAGE, username="test", password="test", dbname="test", driver=None
    )
    _container.start()

    os.environ.update(
        {
            "DATABASE__HOST": _container.get_container_host_ip(),
            "DATABASE__PORT": str(_container.get_exposed_port(5432)),
            "DATABASE__USERNAME": "test",
            "DATABASE__PASSWORD": "test",
            "DATABASE__NAME": "test",
            "AUTH__SERVICE_TOKEN": SERVICE_TOKEN,
        }
    )

    # A separate process keeps Alembic's own event loop away from the tests';
    # `uv run` is not used, it would sync the environment again.
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT_DIR,
        env=os.environ.copy(),
        check=True,
    )


def pytest_unconfigure(config: pytest.Config) -> None:
    if _container is not None:
        _container.stop()


@pytest.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    from magicvibe.core.database.alchemy.setup import url

    test_engine = create_async_engine(url, poolclass=NullPool)
    yield test_engine
    await test_engine.dispose()


@pytest.fixture
async def connection(engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    """One connection per test inside a transaction that is always rolled back."""
    async with engine.connect() as conn:
        transaction = await conn.begin()
        yield conn
        await transaction.rollback()


@pytest.fixture
def session_factory(connection: AsyncConnection) -> async_sessionmaker[AsyncSession]:
    """Sessions bound to the test transaction: a `commit()` only releases a
    savepoint, so nothing reaches the database."""
    return async_sessionmaker(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )


@pytest.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as test_session:
        yield test_session


@pytest.fixture
def uow(session_factory: async_sessionmaker[AsyncSession]) -> UnitOfWork:
    from magicvibe.uow import UnitOfWork

    return UnitOfWork(session_factory=session_factory)


def _override_uow(
    app: FastAPI, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    from magicvibe.dependencies import get_uow
    from magicvibe.uow import UnitOfWork

    app.dependency_overrides[get_uow] = lambda: UnitOfWork(
        session_factory=session_factory
    )


@pytest.fixture
def app(session_factory: async_sessionmaker[AsyncSession]) -> Iterator[FastAPI]:
    from magicvibe.main import app as application

    _override_uow(application, session_factory)
    yield application
    application.dependency_overrides.clear()


def _client(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
        headers=AUTH_HEADERS,
    )


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    """Calls the API as the bot does: with the service token. Tests add
    `X-Telegram-User-Id` themselves."""
    async with _client(app) as test_client:
        yield test_client


@pytest.fixture
async def committed_session_factory(
    engine: AsyncEngine,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Real commits, for `@pytest.mark.concurrency` tests. Every table is
    emptied afterwards, so the next test again starts from an empty database."""
    from magicvibe.core.database.alchemy.models import Base

    yield async_sessionmaker(engine, expire_on_commit=False)

    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
async def concurrent_client(
    committed_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[httpx.AsyncClient]:
    from magicvibe.main import app as application

    _override_uow(application, committed_session_factory)
    async with _client(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()


def acting_user(telegram_id: int) -> dict[str, str]:
    """Headers for a request made on behalf of a user."""
    return {"X-Telegram-User-Id": str(telegram_id)}
