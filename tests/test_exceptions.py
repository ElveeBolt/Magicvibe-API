from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError

from magicvibe.core.exceptions import ErrorCode, ForbiddenError
from magicvibe.exceptions import register_exception_handlers
from magicvibe.middlewares import LoggingMiddleware
from tests.conftest import SERVICE_TOKEN

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

AUTH = {"Authorization": f"Bearer {SERVICE_TOKEN}"}


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """The real application; only requests that fail before any service
    touches the database are sent through it."""
    from magicvibe.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class FakeDriverError(Exception):
    """Stands in for the asyncpg error SQLAlchemy wraps."""

    def __init__(self, constraint_name: str) -> None:
        super().__init__(f"violates constraint {constraint_name}")
        self.constraint_name = constraint_name


def integrity_error(name: str) -> IntegrityError:
    orig = Exception(f"duplicate key value violates {name}")
    orig.__cause__ = FakeDriverError(name)
    return IntegrityError("INSERT ...", {}, orig)


@pytest.fixture
async def handlers_client() -> AsyncIterator[httpx.AsyncClient]:
    """A bare app with the real handlers and middleware and routes that fail on
    purpose."""
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)
    register_exception_handlers(app)

    @app.get("/banned")
    async def banned() -> None:
        raise ForbiddenError(
            "Account is banned",
            code=ErrorCode.USER_BANNED,
            extra={"ban": {"reason": "spam", "comment": None}},
        )

    @app.get("/integrity/{name}")
    async def integrity(name: str) -> None:
        raise integrity_error(name)

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("secret internals")

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def fields(body: dict[str, Any]) -> list[tuple[str, str]]:
    return [(error["field"], error["type"]) for error in body["errors"]]


# Service token


async def test_missing_token(client: httpx.AsyncClient) -> None:
    response = await client.get("/users")

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_SERVICE_TOKEN"
    assert response.headers["WWW-Authenticate"] == "Bearer"


async def test_wrong_token(client: httpx.AsyncClient) -> None:
    response = await client.get("/users", headers={"Authorization": "Bearer nope"})

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_SERVICE_TOKEN"


async def test_token_is_checked_before_the_body(client: httpx.AsyncClient) -> None:
    response = await client.post("/users", json={"unknown": 1})

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_SERVICE_TOKEN"


# Framework errors


async def test_unknown_path(client: httpx.AsyncClient) -> None:
    response = await client.get("/no-such-path", headers=AUTH)

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_wrong_method(client: httpx.AsyncClient) -> None:
    response = await client.put("/users", headers=AUTH)

    assert response.status_code == 405
    assert response.json()["code"] == "METHOD_NOT_ALLOWED"


# Validation errors


async def test_field_too_long(client: httpx.AsyncClient) -> None:
    body = {"telegram": {"telegram_id": 1, "first_name": "x" * 65}}

    response = await client.post("/users", json=body, headers=AUTH)

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert fields(response.json()) == [("telegram.first_name", "string_too_long")]


async def test_unknown_field(client: httpx.AsyncClient) -> None:
    body = {"telegram": {"telegram_id": 1, "first_name": "Ann"}, "extra": 1}

    response = await client.post("/users", json=body, headers=AUTH)

    assert response.status_code == 400
    assert fields(response.json()) == [("extra", "extra_forbidden")]


async def test_nested_field(client: httpx.AsyncClient) -> None:
    body = {"telegram": {"telegram_id": "not-a-number", "first_name": "Ann"}}

    response = await client.post("/users", json=body, headers=AUTH)

    assert response.status_code == 400
    assert fields(response.json()) == [("telegram.telegram_id", "int_parsing")]


async def test_invalid_query_parameter(client: httpx.AsyncClient) -> None:
    response = await client.get("/users", params={"page_size": 101}, headers=AUTH)

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert [field for field, _ in fields(response.json())] == ["page_size"]


async def test_invalid_acting_user_header(client: httpx.AsyncClient) -> None:
    headers = {**AUTH, "X-Telegram-User-Id": "abc"}

    response = await client.get("/discovery/next", headers=headers)

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    [(field, error_type)] = fields(response.json())
    assert field.lower() == "x-telegram-user-id"
    assert error_type == "int_parsing"


# Service errors, constraints, unexpected errors


async def test_service_error_with_extra_fields(
    handlers_client: httpx.AsyncClient,
) -> None:
    response = await handlers_client.get("/banned")

    assert response.status_code == 403
    assert response.json() == {
        "code": "USER_BANNED",
        "detail": "Account is banned",
        "ban": {"reason": "spam", "comment": None},
    }


@pytest.mark.parametrize(
    ("name", "code"),
    [
        ("uq_reaction_pair", "ALREADY_REACTED"),
        ("ix_bans_user_id", "BAN_ALREADY_ACTIVE"),
        ("ck_reactions_not_self", "CONFLICT"),
    ],
)
async def test_integrity_error_by_constraint(
    handlers_client: httpx.AsyncClient, name: str, code: str
) -> None:
    response = await handlers_client.get(f"/integrity/{name}")

    assert response.status_code == 409
    assert response.json()["code"] == code
    assert name not in response.text
    assert "duplicate" not in response.text


async def test_unexpected_error_has_generated_request_id(
    handlers_client: httpx.AsyncClient,
) -> None:
    response = await handlers_client.get("/boom")

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert body["request_id"]
    assert "secret" not in response.text


async def test_unexpected_error_echoes_client_request_id(
    handlers_client: httpx.AsyncClient,
) -> None:
    response = await handlers_client.get("/boom", headers={"X-Request-ID": "abc"})

    assert response.status_code == 500
    assert response.json()["request_id"] == "abc"
