"""Daily limits of likes and superlikes (docs/plans.md → Daily limits)."""

import asyncio
import math
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy import update

from magicvibe.reaction.models import Reaction
from magicvibe.reaction.repositories import DayBounds, ReactionRepository
from tests.conftest import acting_user
from tests.factories import create_reaction, create_subscription, create_user

if TYPE_CHECKING:
    import httpx
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from magicvibe.uow import UnitOfWork
    from magicvibe.user.models import User


def headers(user: User) -> dict[str, str]:
    assert user.telegram is not None
    return acting_user(user.telegram.telegram_id)


async def bounds(session: AsyncSession) -> DayBounds:
    return await ReactionRepository(session).day_bounds()


async def give_likes(
    session: AsyncSession,
    user: User,
    count: int,
    *,
    is_super: bool = False,
    at: datetime | None = None,
) -> list[User]:
    """`count` likes by `user` today (or at `at`), to new users."""
    targets = []
    for _ in range(count):
        target = await create_user(session)
        reaction = await create_reaction(session, user, target, is_super=is_super)
        if at is not None:
            await session.execute(
                update(Reaction).where(Reaction.id == reaction.id).values(created_at=at)
            )
        targets.append(target)
    await session.commit()
    return targets


async def like_someone(
    client: httpx.AsyncClient, session: AsyncSession, user: User, **fields: Any
) -> httpx.Response:
    target = await create_user(session)
    return await client.post(
        "/reactions",
        json={"to_user_id": target.id, "action": "like", **fields},
        headers=headers(user),
    )


async def test_last_like_of_the_day(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await give_likes(session, user, 4)

    assert (await like_someone(client, session, user)).status_code == 201


async def test_like_limit_used_up(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await give_likes(session, user, 5)
    day = await bounds(session)

    response = await like_someone(client, session, user)

    assert response.status_code == 429
    body = response.json()
    assert (body["code"], body["limit_type"]) == ("DAILY_LIMIT_REACHED", "like")
    assert datetime.fromisoformat(body["resets_at"]) == day.next_reset
    assert body["resets_at"].endswith("+00:00")
    expected = math.ceil((day.next_reset - day.at).total_seconds())
    assert response.headers["Retry-After"] == str(expected)


async def test_superlike_on_the_free_plan(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)

    response = await like_someone(client, session, user, is_super=True)

    assert response.status_code == 403
    assert response.json()["code"] == "PREMIUM_REQUIRED"


async def test_superlike_limit_used_up(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_subscription(session, user)
    await give_likes(session, user, 5, is_super=True)

    response = await like_someone(client, session, user, is_super=True)

    assert response.status_code == 429
    assert response.json()["limit_type"] == "superlike"


async def test_superlikes_do_not_use_likes(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_subscription(session, user)
    await give_likes(session, user, 5, is_super=True)

    assert (await like_someone(client, session, user)).status_code == 201


async def test_dislikes_are_unlimited(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await give_likes(session, user, 5)

    response = await like_someone(client, session, user, action="dislike")

    assert response.status_code == 201


@pytest.mark.parametrize(
    ("offset", "status"),
    [(-timedelta(microseconds=1), 201), (timedelta(0), 429)],
    ids=["just-before-midnight", "at-midnight"],
)
async def test_likes_around_midnight(
    client: httpx.AsyncClient,
    session: AsyncSession,
    offset: timedelta,
    status: int,
) -> None:
    user = await create_user(session)
    day = await bounds(session)
    await give_likes(session, user, 5, at=day.day_start + offset)

    assert (await like_someone(client, session, user)).status_code == status


async def test_premium_ended_during_the_day(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_subscription(
        session, user, started=timedelta(days=7), expires_in=-timedelta(seconds=1)
    )
    await give_likes(session, user, 10)

    response = await like_someone(client, session, user)

    assert response.status_code == 429
    assert response.json()["limit_type"] == "like"


async def test_repeated_reaction_at_the_limit(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    [first, *_] = await give_likes(session, user, 5)

    response = await client.post(
        "/reactions",
        json={"to_user_id": first.id, "action": "like"},
        headers=headers(user),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "ALREADY_REACTED"


@pytest.mark.concurrency
async def test_parallel_likes_at_the_limit(
    concurrent_client: httpx.AsyncClient,
    committed_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with committed_session_factory() as session:
        user = await create_user(session)
        await give_likes(session, user, 4)
        targets = [await create_user(session), await create_user(session)]

    responses = await asyncio.gather(
        *(
            concurrent_client.post(
                "/reactions",
                json={"to_user_id": target.id, "action": "like"},
                headers=headers(user),
            )
            for target in targets
        )
    )

    assert sorted(r.status_code for r in responses) == [201, 429]


# The day itself, computed by the database in Europe/Kyiv.


def utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=UTC)


@pytest.mark.parametrize(
    ("at", "day_start", "next_reset"),
    [
        # 23:59:59.999999 and 00:00 Kyiv time in summer (UTC+3).
        (
            utc(2026, 6, 15, 20, 59, 59, 999999),
            utc(2026, 6, 14, 21),
            utc(2026, 6, 15, 21),
        ),
        (utc(2026, 6, 15, 21), utc(2026, 6, 15, 21), utc(2026, 6, 16, 21)),
        # Winter (UTC+2).
        (utc(2026, 1, 10, 12), utc(2026, 1, 9, 22), utc(2026, 1, 10, 22)),
    ],
    ids=["summer-last-microsecond", "summer-midnight", "winter"],
)
async def test_day_bounds(
    uow: UnitOfWork, at: datetime, day_start: datetime, next_reset: datetime
) -> None:
    async with uow:
        day = await uow.reaction.day_bounds(at)

    assert (day.day_start, day.next_reset) == (day_start, next_reset)


@pytest.mark.parametrize(
    ("at", "hours"),
    [(utc(2026, 3, 29, 12), 23), (utc(2026, 10, 25, 12), 25)],
    ids=["spring-forward", "fall-back"],
)
async def test_days_around_daylight_saving_time(
    uow: UnitOfWork, at: datetime, hours: int
) -> None:
    async with uow:
        day = await uow.reaction.day_bounds(at)

    assert day.next_reset - day.day_start == timedelta(hours=hours)
