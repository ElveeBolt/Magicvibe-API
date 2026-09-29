import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import func, select, update

from magicvibe.subscription.models import Subscription
from tests.factories import create_ban, create_subscription, create_user

if TYPE_CHECKING:
    import httpx
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def grant(user_id: int, **fields: object) -> dict[str, object]:
    return {"user_id": user_id, **fields}


# Granting


async def test_grant_premium(client: httpx.AsyncClient, session: AsyncSession) -> None:
    user = await create_user(session)

    response = await client.post("/subscriptions", json=grant(user.id, comment="Paid"))

    assert response.status_code == 201
    body = response.json()
    assert body["plan"] == "premium"
    assert body["comment"] == "Paid"
    starts = datetime.fromisoformat(body["starts_at"])
    assert datetime.fromisoformat(body["expires_at"]) - starts == timedelta(days=7)


async def test_premium_already_current(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_subscription(session, user)

    response = await client.post("/subscriptions", json=grant(user.id))

    assert response.status_code == 409
    assert response.json()["code"] == "PREMIUM_ALREADY_ACTIVE"


async def test_banned_user(client: httpx.AsyncClient, session: AsyncSession) -> None:
    user = await create_user(session)
    await create_ban(session, user)

    response = await client.post("/subscriptions", json=grant(user.id))

    assert response.status_code == 409
    assert response.json()["code"] == "TARGET_USER_BANNED"


async def test_unknown_user(client: httpx.AsyncClient) -> None:
    response = await client.post("/subscriptions", json=grant(999_999))

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_free_plan_cannot_be_granted(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)

    response = await client.post("/subscriptions", json=grant(user.id, plan="free"))

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_start_time_from_the_request(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)

    response = await client.post(
        "/subscriptions",
        json=grant(user.id, starts_at="2099-01-01T00:00:00Z"),
    )

    assert response.status_code == 400
    assert [(e["field"], e["type"]) for e in response.json()["errors"]] == [
        ("starts_at", "extra_forbidden")
    ]


async def test_grant_again_after_the_period(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_subscription(
        session, user, started=timedelta(days=8), expires_in=-timedelta(days=1)
    )

    response = await client.post("/subscriptions", json=grant(user.id))

    assert response.status_code == 201


@pytest.mark.concurrency
async def test_simultaneous_grants(
    concurrent_client: httpx.AsyncClient,
    committed_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with committed_session_factory() as session:
        user = await create_user(session)

    responses = await asyncio.gather(
        *(
            concurrent_client.post("/subscriptions", json=grant(user.id))
            for _ in range(2)
        )
    )

    assert sorted(r.status_code for r in responses) == [201, 409]
    [rejected] = [r for r in responses if r.status_code == 409]
    assert rejected.json()["code"] == "PREMIUM_ALREADY_ACTIVE"
    async with committed_session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(Subscription))
    assert count == 1


# Ending


async def test_end_early(client: httpx.AsyncClient, session: AsyncSession) -> None:
    user = await create_user(session)
    subscription = await create_subscription(session, user)

    response = await client.post(f"/subscriptions/{subscription.id}/end")

    assert response.status_code == 200
    assert (await client.get(f"/users/{user.id}/plan")).json()["code"] == "free"


async def test_end_an_ended_subscription(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    subscription = await create_subscription(
        session,
        await create_user(session),
        started=timedelta(days=8),
        expires_in=-timedelta(days=1),
    )

    response = await client.post(f"/subscriptions/{subscription.id}/end")

    assert response.status_code == 409
    assert response.json()["code"] == "CONFLICT"


async def test_end_unknown_subscription(client: httpx.AsyncClient) -> None:
    response = await client.post("/subscriptions/999999/end")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


# Effective plan


async def test_free_user_plan(client: httpx.AsyncClient, session: AsyncSession) -> None:
    user = await create_user(session)

    response = await client.get(f"/users/{user.id}/plan")

    assert response.status_code == 200
    assert response.json() == {
        "code": "free",
        "name": "Free",
        "daily_like_limit": 5,
        "daily_superlike_limit": 0,
        "can_see_likers": False,
        "expires_at": None,
    }


async def test_premium_user_plan(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    subscription = await create_subscription(session, user)

    body = (await client.get(f"/users/{user.id}/plan")).json()

    assert (body["code"], body["daily_like_limit"], body["daily_superlike_limit"]) == (
        "premium",
        20,
        5,
    )
    assert body["can_see_likers"] is True
    assert datetime.fromisoformat(body["expires_at"]) == subscription.expires_at


async def test_plan_at_the_end_of_the_period(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    subscription = await create_subscription(session, user)
    await session.execute(
        update(Subscription)
        .where(Subscription.id == subscription.id)
        .values(expires_at=func.now())
    )
    await session.commit()

    assert (await client.get(f"/users/{user.id}/plan")).json()["code"] == "free"


async def test_plan_of_an_unknown_user(client: httpx.AsyncClient) -> None:
    response = await client.get("/users/999999/plan")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


# Listing


async def test_a_users_subscriptions(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user, other = await create_user(session), await create_user(session)
    old = await create_subscription(
        session, user, started=timedelta(days=20), expires_in=-timedelta(days=13)
    )
    await session.execute(
        update(Subscription)
        .where(Subscription.id == old.id)
        .values(created_at=func.now() - timedelta(days=20))
    )
    new = await create_subscription(session, user)
    await create_subscription(session, other)

    response = await client.get("/subscriptions", params={"user_id": user.id})

    assert [item["id"] for item in response.json()["items"]] == [new.id, old.id]


async def test_get_one_subscription(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    subscription = await create_subscription(session, await create_user(session))

    assert (await client.get(f"/subscriptions/{subscription.id}")).status_code == 200
    assert (await client.get("/subscriptions/999999")).status_code == 404
