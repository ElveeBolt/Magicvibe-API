import asyncio
from typing import TYPE_CHECKING

import pytest

from tests.factories import create_user

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
