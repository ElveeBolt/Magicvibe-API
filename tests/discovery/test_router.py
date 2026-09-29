from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

import pytest

from magicvibe.reaction.enums import ReactionAction
from magicvibe.user.enums import DatingGoal, UserProfileGender
from tests.conftest import acting_user
from tests.factories import (
    create_ban,
    create_city,
    create_preference,
    create_profile,
    create_reaction,
    create_region,
    create_report,
    create_user,
)

if TYPE_CHECKING:
    import httpx
    from sqlalchemy.ext.asyncio import AsyncSession

    from magicvibe.region.models import RegionCity
    from magicvibe.user.models import User

MALE, FEMALE = UserProfileGender.MALE, UserProfileGender.FEMALE
ANY: dict[str, Any] = {}


def years_ago(years: int) -> date:
    today = datetime.now(UTC).date()
    try:
        return today.replace(year=today.year - years)
    except ValueError:  # 29 February
        return today.replace(year=today.year - years, day=28)


async def person(
    session: AsyncSession,
    city: RegionCity,
    *,
    gender: UserProfileGender,
    age: int = 30,
    goal: DatingGoal = DatingGoal.RELATIONSHIP,
    wants: dict[str, Any] | None = ANY,
    visible: bool = True,
) -> User:
    """A user with a complete profile and, unless `wants` is None, preferences
    (`wants` holds the criteria that are not "any")."""
    user = await create_user(session)
    await create_profile(
        session,
        user,
        gender=gender,
        birth_date=years_ago(age),
        city=city,
        dating_goal=goal,
        is_visible=visible,
    )
    if wants is not None:
        await create_preference(session, user, **wants)
    return user


def headers(user: User) -> dict[str, str]:
    assert user.telegram is not None
    return acting_user(user.telegram.telegram_id)


@pytest.fixture
async def city(session: AsyncSession) -> RegionCity:
    return await create_city(session, await create_region(session), name="Черкаси")


@pytest.fixture
async def other_city(session: AsyncSession) -> RegionCity:
    return await create_city(session, await create_region(session), name="Умань")


async def next_for(client: httpx.AsyncClient, user: User) -> Any:
    response = await client.get("/discovery/next", headers=headers(user))
    assert response.status_code == 200, response.json()
    return response.json()


# Who may browse


async def test_no_profile(client: httpx.AsyncClient, session: AsyncSession) -> None:
    viewer = await create_user(session)

    response = await client.get("/discovery/next", headers=headers(viewer))

    assert response.status_code == 409
    assert response.json()["code"] == "PROFILE_REQUIRED"


async def test_no_preferences(
    client: httpx.AsyncClient, session: AsyncSession, city: RegionCity
) -> None:
    viewer = await person(session, city, gender=MALE, wants=None)

    response = await client.get("/discovery/next", headers=headers(viewer))

    assert response.status_code == 409
    assert response.json()["code"] == "PREFERENCES_REQUIRED"


async def test_hidden_user_browses(
    client: httpx.AsyncClient, session: AsyncSession, city: RegionCity
) -> None:
    viewer = await person(session, city, gender=MALE, visible=False)
    candidate = await person(session, city, gender=FEMALE)

    assert (await next_for(client, viewer))["id"] == candidate.id


# Candidates


async def test_banned_user_is_not_shown(
    client: httpx.AsyncClient, session: AsyncSession, city: RegionCity
) -> None:
    viewer = await person(session, city, gender=MALE)
    await create_ban(session, await person(session, city, gender=FEMALE))

    assert await next_for(client, viewer) is None


async def test_hidden_profile_is_not_shown(
    client: httpx.AsyncClient, session: AsyncSession, city: RegionCity
) -> None:
    viewer = await person(session, city, gender=MALE)
    await person(session, city, gender=FEMALE, visible=False)

    assert await next_for(client, viewer) is None


async def test_candidate_without_preferences_is_not_shown(
    client: httpx.AsyncClient, session: AsyncSession, city: RegionCity
) -> None:
    viewer = await person(session, city, gender=MALE)
    await person(session, city, gender=FEMALE, wants=None)

    assert await next_for(client, viewer) is None


@pytest.mark.parametrize("action", [ReactionAction.LIKE, ReactionAction.DISLIKE])
async def test_already_reacted_is_not_shown(
    client: httpx.AsyncClient,
    session: AsyncSession,
    city: RegionCity,
    action: ReactionAction,
) -> None:
    viewer = await person(session, city, gender=MALE)
    candidate = await person(session, city, gender=FEMALE)
    await create_reaction(session, viewer, candidate, action=action)

    assert await next_for(client, viewer) is None


@pytest.mark.parametrize(
    "criterion", ["gender", "age", "city", "dating_goal"], ids=lambda c: c
)
async def test_not_what_the_acting_user_wants(
    client: httpx.AsyncClient,
    session: AsyncSession,
    city: RegionCity,
    other_city: RegionCity,
    criterion: str,
) -> None:
    wants = {
        "gender": {"gender": MALE},
        "age": {"max_age": 29},
        "city": {"city": other_city},
        "dating_goal": {"dating_goal": DatingGoal.CASUAL},
    }[criterion]
    viewer = await person(session, city, gender=MALE, wants=wants)
    await person(session, city, gender=FEMALE)

    assert await next_for(client, viewer) is None


@pytest.mark.parametrize(
    "criterion", ["gender", "age", "city", "dating_goal"], ids=lambda c: c
)
async def test_not_what_the_candidate_wants(
    client: httpx.AsyncClient,
    session: AsyncSession,
    city: RegionCity,
    other_city: RegionCity,
    criterion: str,
) -> None:
    wants = {
        "gender": {"gender": FEMALE},
        "age": {"max_age": 29},
        "city": {"city": other_city},
        "dating_goal": {"dating_goal": DatingGoal.CASUAL},
    }[criterion]
    viewer = await person(session, city, gender=MALE)
    await person(session, city, gender=FEMALE, wants=wants)

    assert await next_for(client, viewer) is None


async def test_any_in_preferences_both_ways(
    client: httpx.AsyncClient,
    session: AsyncSession,
    city: RegionCity,
    other_city: RegionCity,
) -> None:
    first = await person(session, city, gender=MALE, goal=DatingGoal.CASUAL)
    second = await person(session, other_city, gender=FEMALE, age=45)

    assert (await next_for(client, first))["id"] == second.id
    assert (await next_for(client, second))["id"] == first.id


@pytest.mark.parametrize("bound", ["min_age", "max_age"])
async def test_age_range_boundaries(
    client: httpx.AsyncClient, session: AsyncSession, city: RegionCity, bound: str
) -> None:
    other_bound = {"min_age": {"max_age": 100}, "max_age": {"min_age": 18}}[bound]
    viewer = await person(session, city, gender=MALE, wants={bound: 25, **other_bound})
    candidate = await person(session, city, gender=FEMALE, age=25)

    assert (await next_for(client, viewer))["id"] == candidate.id


async def test_reported_user_is_still_shown(
    client: httpx.AsyncClient, session: AsyncSession, city: RegionCity
) -> None:
    viewer = await person(session, city, gender=MALE)
    candidate = await person(session, city, gender=FEMALE)
    await create_report(session, viewer, candidate)

    assert (await next_for(client, viewer))["id"] == candidate.id


# Order and response


async def test_public_profile(
    client: httpx.AsyncClient, session: AsyncSession, city: RegionCity
) -> None:
    viewer = await person(session, city, gender=MALE)
    await person(session, city, gender=FEMALE)

    body = await next_for(client, viewer)

    assert set(body) == {"id", "last_seen_at", "profile"}
    assert body["profile"]["city"]["name"] == "Черкаси"
    assert "telegram" not in str(body)
    assert "username" not in str(body)


async def test_nobody_left(
    client: httpx.AsyncClient, session: AsyncSession, city: RegionCity
) -> None:
    viewer = await person(session, city, gender=MALE)

    response = await client.get("/discovery/next", headers=headers(viewer))

    assert response.status_code == 200
    assert response.text == "null"


async def test_random_order(
    client: httpx.AsyncClient, session: AsyncSession, city: RegionCity
) -> None:
    viewer = await person(session, city, gender=MALE)
    candidates = {
        (await person(session, city, gender=FEMALE)).id,
        (await person(session, city, gender=FEMALE)).id,
    }

    # Missing one of two equally likely candidates in 40 draws has a chance
    # of 2 * 0.5**40.
    seen = {(await next_for(client, viewer))["id"] for _ in range(40)}

    assert seen == candidates
