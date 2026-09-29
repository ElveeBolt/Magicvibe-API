import asyncio
from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import func, update

from magicvibe.ban.models import Ban
from tests.conftest import acting_user
from tests.factories import create_ban, create_user

if TYPE_CHECKING:
    import httpx
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@pytest.mark.concurrency
async def test_simultaneous_bans_create_exactly_one(
    concurrent_client: httpx.AsyncClient,
    committed_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with committed_session_factory() as session:
        user = await create_user(session)

    body = {"user_id": user.id, "reason": "spam"}
    responses = await asyncio.gather(
        concurrent_client.post("/bans", json=body),
        concurrent_client.post("/bans", json=body),
    )

    statuses = sorted(response.status_code for response in responses)
    assert statuses == [201, 409]
    [rejected] = [r for r in responses if r.status_code == 409]
    assert rejected.json()["code"] == "BAN_ALREADY_ACTIVE"


async def test_ban_a_user(client: httpx.AsyncClient, session: AsyncSession) -> None:
    user = await create_user(session)

    response = await client.post("/bans", json={"user_id": user.id, "reason": "spam"})

    assert response.status_code == 201
    assert response.json()["lifted_at"] is None
    assert "expires_at" not in response.json()
    assert (await client.get(f"/users/{user.id}")).json()["status"] == "banned"


async def test_ban_has_no_end_date(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)

    response = await client.post(
        "/bans",
        json={
            "user_id": user.id,
            "reason": "spam",
            "expires_at": "2099-01-01T00:00:00Z",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert [(e["field"], e["type"]) for e in response.json()["errors"]] == [
        ("expires_at", "extra_forbidden")
    ]


async def test_second_active_ban(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_ban(session, user)

    response = await client.post("/bans", json={"user_id": user.id, "reason": "spam"})

    assert response.status_code == 409
    assert response.json()["code"] == "BAN_ALREADY_ACTIVE"


async def test_ban_unknown_user(client: httpx.AsyncClient) -> None:
    response = await client.post("/bans", json={"user_id": 999_999, "reason": "spam"})

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_lift_a_ban(client: httpx.AsyncClient, session: AsyncSession) -> None:
    user = await create_user(session)
    ban = await create_ban(session, user)

    response = await client.post(
        f"/bans/{ban.id}/lift", json={"lift_comment": "Mistake"}
    )

    assert response.status_code == 200
    assert response.json()["lifted_at"] is not None
    assert response.json()["lift_comment"] == "Mistake"
    assert (await client.get(f"/users/{user.id}")).json()["status"] == "active"


async def test_lift_twice(client: httpx.AsyncClient, session: AsyncSession) -> None:
    ban = await create_ban(session, await create_user(session), lifted=True)

    response = await client.post(f"/bans/{ban.id}/lift", json={})

    assert response.status_code == 409
    assert response.json()["code"] == "CONFLICT"


async def test_ban_again_after_a_lift(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_ban(session, user, lifted=True)

    response = await client.post("/bans", json={"user_id": user.id, "reason": "scam"})

    assert response.status_code == 201
    assert (await client.get(f"/users/{user.id}")).json()["status"] == "banned"


async def test_old_ban_still_blocks_the_user(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    ban = await create_ban(session, user, comment="Spam links")
    await session.execute(
        update(Ban)
        .where(Ban.id == ban.id)
        .values(created_at=func.now() - timedelta(days=3650))
    )
    await session.commit()
    assert user.telegram is not None

    response = await client.get(
        "/discovery/next", headers=acting_user(user.telegram.telegram_id)
    )

    assert response.status_code == 403
    assert response.json()["ban"] == {"reason": "spam", "comment": "Spam links"}
