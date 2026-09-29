import asyncio
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import func, or_, select, text

from magicvibe.ban.enums import BanReason
from magicvibe.ban.models import Ban
from magicvibe.reaction.models import Reaction
from magicvibe.report.models import Report
from magicvibe.user.models import User, UserPreference, UserProfile, UserTelegram
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
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Any endpoint that needs the acting user works here; discovery needs no body.
ACTING_USER_ENDPOINT = "/discovery/next"


def registration(telegram_id: int, first_name: str = "Ann") -> dict[str, object]:
    return {"telegram": {"telegram_id": telegram_id, "first_name": first_name}}


async def telegram_id_of(user: User) -> int:
    assert user.telegram is not None
    return user.telegram.telegram_id


# Acting user


async def test_unknown_acting_user(client: httpx.AsyncClient) -> None:
    response = await client.get(ACTING_USER_ENDPOINT, headers=acting_user(999_999))

    assert response.status_code == 404
    assert response.json()["code"] == "USER_NOT_FOUND"


async def test_deleted_acting_user(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    telegram_id = await telegram_id_of(user)
    assert (await client.delete(f"/users/{user.id}")).status_code == 204

    response = await client.get(ACTING_USER_ENDPOINT, headers=acting_user(telegram_id))

    assert response.status_code == 404
    assert response.json()["code"] == "USER_NOT_FOUND"


async def test_banned_acting_user(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_ban(session, user, reason=BanReason.SCAM, comment="Fake shop")

    response = await client.get(
        ACTING_USER_ENDPOINT, headers=acting_user(await telegram_id_of(user))
    )

    assert response.status_code == 403
    body = response.json()
    assert body["code"] == "USER_BANNED"
    assert body["ban"] == {"reason": "scam", "comment": "Fake shop"}


# Registration and refresh


async def test_register_new_telegram_account(client: httpx.AsyncClient) -> None:
    response = await client.post("/users", json=registration(5001))

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "active"
    assert body["telegram"]["telegram_id"] == 5001
    assert "deleted_at" not in body


async def test_returning_user_gets_telegram_data_refreshed(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session, telegram_id=5002, first_name="Old")

    response = await client.post("/users", json=registration(5002, "New"))

    assert response.status_code == 200
    assert response.json()["id"] == user.id
    assert response.json()["telegram"]["first_name"] == "New"


async def test_banned_user_start_keeps_telegram_data(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session, telegram_id=5003, first_name="Old")
    await create_ban(session, user, reason=BanReason.SPAM, comment=None)

    response = await client.post("/users", json=registration(5003, "New"))

    assert response.status_code == 403
    assert response.json()["code"] == "USER_BANNED"
    assert response.json()["ban"] == {"reason": "spam", "comment": None}
    telegram = await client.get(f"/users/{user.id}/telegram")
    assert telegram.json()["first_name"] == "Old"


async def test_start_after_deletion_creates_a_new_account(
    client: httpx.AsyncClient,
) -> None:
    first = await client.post("/users", json=registration(5004))
    assert (await client.delete(f"/users/{first.json()['id']}")).status_code == 204

    second = await client.post("/users", json=registration(5004))

    assert second.status_code == 201
    assert second.json()["id"] != first.json()["id"]


# Deletion


async def test_delete_removes_all_data_of_the_user(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    other = await create_user(session)
    await create_profile(session, user)
    await create_preference(session, user)
    await create_reaction(session, user, other)
    await create_reaction(session, other, user)
    await create_report(session, user, other)
    await create_report(session, other, user)
    await create_ban(session, user, lifted=True)

    response = await client.delete(f"/users/{user.id}")

    assert response.status_code == 204
    counts = {
        model.__tablename__: await session.scalar(
            select(func.count()).select_from(model).where(condition)
        )
        for model, condition in [
            (User, User.id == user.id),
            (UserTelegram, UserTelegram.user_id == user.id),
            (UserProfile, UserProfile.user_id == user.id),
            (UserPreference, UserPreference.user_id == user.id),
            (
                Reaction,
                or_(Reaction.from_user_id == user.id, Reaction.to_user_id == user.id),
            ),
            (Report, or_(Report.reporter_id == user.id, Report.target_id == user.id)),
            (Ban, Ban.user_id == user.id),
        ]
    }
    assert set(counts.values()) == {0}, counts


async def test_delete_keeps_other_users_data(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    deleted = await create_user(session)
    other = await create_user(session)
    third = await create_user(session)
    await create_reaction(session, deleted, other)
    await create_reaction(session, other, third)

    response = await client.delete(f"/users/{deleted.id}")

    assert response.status_code == 204
    assert await session.get(User, other.id) is not None
    assert await session.get(User, third.id) is not None
    remaining = await session.scalar(
        select(func.count())
        .select_from(Reaction)
        .where(Reaction.from_user_id == other.id, Reaction.to_user_id == third.id)
    )
    assert remaining == 1


async def test_banned_account_cannot_be_deleted(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_ban(session, user, reason=BanReason.HARASSMENT, comment="Threats")

    response = await client.delete(f"/users/{user.id}")

    assert response.status_code == 403
    assert response.json()["code"] == "USER_BANNED"
    assert response.json()["ban"] == {"reason": "harassment", "comment": "Threats"}
    assert (await client.get(f"/users/{user.id}")).status_code == 200


async def test_delete_unknown_account(client: httpx.AsyncClient) -> None:
    response = await client.delete("/users/999999")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_there_is_no_restore(client: httpx.AsyncClient) -> None:
    response = await client.post("/users/1/restore")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


@pytest.mark.concurrency
async def test_ban_and_deletion_at_the_same_time(
    concurrent_client: httpx.AsyncClient,
    committed_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with committed_session_factory() as session:
        user = await create_user(session)

    ban, deletion = await asyncio.gather(
        concurrent_client.post("/bans", json={"user_id": user.id, "reason": "spam"}),
        concurrent_client.delete(f"/users/{user.id}"),
    )

    async with committed_session_factory() as session:
        user_exists = await session.get(User, user.id) is not None
    if ban.status_code == 201:
        assert deletion.status_code == 403
        assert deletion.json()["code"] == "USER_BANNED"
        assert user_exists
    else:
        assert (ban.status_code, deletion.status_code) == (404, 204)
        assert not user_exists


# Status


async def test_status_cannot_be_set_through_the_api(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)

    response = await client.patch(f"/users/{user.id}", json={"status": "banned"})

    assert response.status_code == 405
    assert response.json()["code"] == "METHOD_NOT_ALLOWED"


# Last online time


async def last_seen_is_now(session: AsyncSession, user: User) -> bool:
    return bool(
        await session.scalar(
            select(User.last_seen_at == func.now()).where(User.id == user.id)
        )
    )


@pytest.mark.parametrize(
    ("age", "updated"), [("2 minutes", True), ("10 seconds", False)]
)
async def test_last_seen_is_updated_at_most_once_a_minute(
    client: httpx.AsyncClient, session: AsyncSession, age: str, updated: bool
) -> None:
    user = await create_user(session)
    # `now()` is fixed for the whole test transaction, so the stored value is
    # set relative to it and no real time has to pass.
    await session.execute(
        text(
            f"UPDATE users SET last_seen_at = now() - interval '{age}' WHERE id = :id"
        ),
        {"id": user.id},
    )
    await session.commit()

    await client.get(
        ACTING_USER_ENDPOINT, headers=acting_user(await telegram_id_of(user))
    )

    assert await last_seen_is_now(session, user) is updated


# Profile


def profile_body(city_id: int, **fields: object) -> dict[str, object]:
    return {
        "name": "Ann",
        "birth_date": "2000-01-01",
        "gender": "female",
        "city_id": city_id,
        "dating_goal": "relationship",
        **fields,
    }


def error_fields(response: httpx.Response) -> list[tuple[str, str]]:
    return [(e["field"], e["type"]) for e in response.json()["errors"]]


async def test_complete_profile_without_bio(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    city = await create_city(session, await create_region(session), name="Черкаси")

    response = await client.put(f"/users/{user.id}/profile", json=profile_body(city.id))

    assert response.status_code == 200
    body = response.json()
    assert body["bio"] is None
    assert body["is_visible"] is True
    assert body["dating_goal"] == "relationship"
    assert body["city_id"] == city.id
    assert body["city"]["name"] == "Черкаси"
    assert isinstance(body["age"], int)


async def test_profile_without_dating_goal(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    city = await create_city(session, await create_region(session))
    body = profile_body(city.id)
    del body["dating_goal"]

    response = await client.put(f"/users/{user.id}/profile", json=body)

    assert response.status_code == 400
    assert error_fields(response) == [("dating_goal", "missing")]


async def test_profile_with_unknown_dating_goal(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    city = await create_city(session, await create_region(session))

    response = await client.put(
        f"/users/{user.id}/profile",
        json=profile_body(city.id, dating_goal="marriage"),
    )

    assert response.status_code == 400
    assert [field for field, _ in error_fields(response)] == ["dating_goal"]


async def test_profile_with_unknown_city(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)

    response = await client.put(f"/users/{user.id}/profile", json=profile_body(999_999))

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


@pytest.mark.parametrize("bio", ["", "   "])
async def test_profile_with_empty_bio(
    client: httpx.AsyncClient, session: AsyncSession, bio: str
) -> None:
    user = await create_user(session)
    city = await create_city(session, await create_region(session))

    response = await client.put(
        f"/users/{user.id}/profile", json=profile_body(city.id, bio=bio)
    )

    assert response.status_code == 400
    assert [field for field, _ in error_fields(response)] == ["bio"]


async def test_profile_with_bio_too_long(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    city = await create_city(session, await create_region(session))

    response = await client.put(
        f"/users/{user.id}/profile", json=profile_body(city.id, bio="x" * 501)
    )

    assert response.status_code == 400
    assert error_fields(response) == [("bio", "string_too_long")]


async def test_profile_does_not_create_preferences(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    city = await create_city(session, await create_region(session))
    await client.put(f"/users/{user.id}/profile", json=profile_body(city.id))

    response = await client.get(f"/users/{user.id}/preferences")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_change_the_city(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_profile(session, user, name="Olena")
    other_city = await create_city(session, await create_region(session), name="Умань")

    response = await client.patch(
        f"/users/{user.id}/profile", json={"city_id": other_city.id}
    )

    assert response.status_code == 200
    assert response.json()["city"]["name"] == "Умань"
    assert response.json()["name"] == "Olena"


async def test_change_to_an_unknown_city(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_profile(session, user)

    response = await client.patch(
        f"/users/{user.id}/profile", json={"city_id": 999_999}
    )

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_remove_the_bio(client: httpx.AsyncClient, session: AsyncSession) -> None:
    user = await create_user(session)
    await create_profile(session, user, bio="Hello")

    response = await client.patch(f"/users/{user.id}/profile", json={"bio": None})

    assert response.status_code == 200
    assert response.json()["bio"] is None


async def test_required_field_cannot_be_null(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_profile(session, user)

    response = await client.patch(
        f"/users/{user.id}/profile", json={"dating_goal": None}
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


# Preferences


async def test_preferences_with_any_city_and_goal(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)

    response = await client.put(
        f"/users/{user.id}/preferences", json={"gender": "male"}
    )

    assert response.status_code == 200
    body = response.json()
    assert (body["city_id"], body["city"], body["dating_goal"]) == (None, None, None)
    assert (body["min_age"], body["max_age"]) == (18, 100)


async def test_preferences_with_one_city_and_goal(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    city = await create_city(session, await create_region(session), name="Львів")

    response = await client.put(
        f"/users/{user.id}/preferences",
        json={"city_id": city.id, "dating_goal": "friendship"},
    )

    assert response.status_code == 200
    assert response.json()["city"]["name"] == "Львів"
    assert response.json()["dating_goal"] == "friendship"


async def test_preferences_with_unknown_city(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)

    response = await client.put(
        f"/users/{user.id}/preferences", json={"city_id": 999_999}
    )

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_preferences_with_reversed_age_range(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)

    response = await client.put(
        f"/users/{user.id}/preferences", json={"min_age": 30, "max_age": 20}
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_preferences_back_to_any_city(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    city = await create_city(session, await create_region(session))
    await create_preference(session, user, city=city)

    response = await client.patch(
        f"/users/{user.id}/preferences", json={"city_id": None}
    )

    assert response.status_code == 200
    assert response.json()["city_id"] is None


async def test_preferences_merged_age_range(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_preference(session, user, max_age=25)

    response = await client.patch(f"/users/{user.id}/preferences", json={"min_age": 30})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
