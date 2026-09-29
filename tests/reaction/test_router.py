import asyncio
from datetime import timedelta
from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy import func, select, update

from magicvibe.reaction.enums import ReactionAction
from magicvibe.reaction.models import Match, Reaction
from tests.conftest import acting_user
from tests.factories import (
    create_ban,
    create_match,
    create_profile,
    create_reaction,
    create_subscription,
    create_user,
)

if TYPE_CHECKING:
    import httpx
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from magicvibe.user.models import User


def headers(user: User) -> dict[str, str]:
    assert user.telegram is not None
    return acting_user(user.telegram.telegram_id)


async def react(
    client: httpx.AsyncClient, user: User, target_id: int, **fields: Any
) -> httpx.Response:
    return await client.post(
        "/reactions",
        json={"to_user_id": target_id, "action": "like", **fields},
        headers=headers(user),
    )


async def user_with_profile(session: AsyncSession, **fields: Any) -> User:
    user = await create_user(session, **fields)
    await create_profile(session, user)
    return user


async def count_matches(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(Match)) or 0


# Reacting


async def test_like_with_a_message(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user, target = await create_user(session), await create_user(session)

    response = await react(client, user, target.id, message="Hi!")

    assert response.status_code == 201
    body = response.json()
    assert body["reaction"]["message"] == "Hi!"
    assert body["match"] is None


async def test_superlike(client: httpx.AsyncClient, session: AsyncSession) -> None:
    user, target = await create_user(session), await create_user(session)
    await create_subscription(session, user)

    response = await react(client, user, target.id, is_super=True)

    assert response.status_code == 201
    assert response.json()["reaction"]["is_super"] is True


async def test_dislike_with_a_message(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user, target = await create_user(session), await create_user(session)

    response = await react(client, user, target.id, action="dislike", message="No")

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("message", ["", "   "])
async def test_empty_message(
    client: httpx.AsyncClient, session: AsyncSession, message: str
) -> None:
    user, target = await create_user(session), await create_user(session)

    response = await react(client, user, target.id, message=message)

    assert response.status_code == 400
    assert [e["field"] for e in response.json()["errors"]] == ["message"]


async def test_repeated_reaction(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user, target = await create_user(session), await create_user(session)
    await create_reaction(session, user, target, action=ReactionAction.DISLIKE)

    response = await react(client, user, target.id)

    assert response.status_code == 409
    assert response.json()["code"] == "ALREADY_REACTED"


async def test_reaction_to_oneself(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)

    response = await react(client, user, user.id)

    assert response.status_code == 400
    assert response.json()["code"] == "SELF_ACTION"


@pytest.mark.parametrize("target", ["unknown", "banned"])
async def test_unknown_or_banned_target(
    client: httpx.AsyncClient, session: AsyncSession, target: str
) -> None:
    user = await create_user(session)
    if target == "banned":
        banned = await create_user(session)
        await create_ban(session, banned)
        target_id = banned.id
    else:
        target_id = 999_999

    response = await react(client, user, target_id)

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
    assert await session.scalar(select(func.count()).select_from(Reaction)) == 0


# Mutual like


@pytest.mark.parametrize("first_is_super", [False, True], ids=["like", "superlike"])
async def test_like_back_creates_a_match(
    client: httpx.AsyncClient, session: AsyncSession, first_is_super: bool
) -> None:
    a = await user_with_profile(session, username="ann")
    b = await user_with_profile(session)
    await create_reaction(session, a, b, is_super=first_is_super, message="Coffee?")

    response = await react(client, b, a.id)

    assert response.status_code == 201
    match = response.json()["match"]
    assert match["user"]["id"] == a.id
    assert match["contact"]["username"] == "ann"
    assert match["message"] == "Coffee?"
    assert match["is_super"] is first_is_super
    assert await count_matches(session) == 1


async def test_dislike_back_creates_no_match(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    a, b = await create_user(session), await create_user(session)
    await create_reaction(session, a, b)

    response = await react(client, b, a.id, action="dislike")

    assert response.json()["match"] is None
    assert await count_matches(session) == 0


@pytest.mark.concurrency
async def test_opposite_likes_at_the_same_time(
    concurrent_client: httpx.AsyncClient,
    committed_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with committed_session_factory() as session:
        a = await user_with_profile(session)
        b = await user_with_profile(session)

    responses = await asyncio.gather(
        react(concurrent_client, a, b.id), react(concurrent_client, b, a.id)
    )

    assert [r.status_code for r in responses] == [201, 201]
    assert sum(r.json()["match"] is not None for r in responses) == 1
    async with committed_session_factory() as session:
        assert await count_matches(session) == 1


# Matches


async def matched(session: AsyncSession, a: User, b: User, **a_like: Any) -> Match:
    await create_reaction(session, a, b, **a_like)
    await create_reaction(session, b, a)
    return await create_match(session, a, b)


async def matches_of(client: httpx.AsyncClient, user: User) -> Any:
    response = await client.get("/matches", headers=headers(user))
    assert response.status_code == 200
    return response.json()


async def test_partner_message_after_the_match(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    a, b = await user_with_profile(session), await user_with_profile(session)
    await matched(session, a, b, message="From A")

    [b_sees] = (await matches_of(client, b))["items"]
    [a_sees] = (await matches_of(client, a))["items"]

    assert (b_sees["user"]["id"], b_sees["message"]) == (a.id, "From A")
    assert (a_sees["user"]["id"], a_sees["message"]) == (b.id, None)
    assert set(a_sees["contact"]) == {
        "telegram_id",
        "first_name",
        "last_name",
        "username",
    }


async def test_no_contact_or_message_outside_matches(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    a, b = await user_with_profile(session), await user_with_profile(session)

    response = await react(client, a, b.id, message="Secret words")

    assert "telegram" not in response.text
    assert "contact" not in response.text


async def test_newest_first(client: httpx.AsyncClient, session: AsyncSession) -> None:
    me = await user_with_profile(session)
    older, newer = await user_with_profile(session), await user_with_profile(session)
    first = await matched(session, me, older)
    await matched(session, me, newer)
    await session.execute(
        update(Match)
        .where(Match.id == first.id)
        .values(created_at=func.now() - timedelta(days=1))
    )
    await session.commit()

    items = (await matches_of(client, me))["items"]

    assert [item["user"]["id"] for item in items] == [newer.id, older.id]


async def test_banned_partner_is_hidden_until_lifted(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    me, partner = await user_with_profile(session), await user_with_profile(session)
    await matched(session, me, partner)
    ban = await create_ban(session, partner)

    hidden = await matches_of(client, me)
    lift = await client.post(f"/bans/{ban.id}/lift", json={})
    shown = await matches_of(client, me)

    assert (hidden["items"], hidden["total"]) == ([], 0)
    assert lift.status_code == 200
    assert [item["user"]["id"] for item in shown["items"]] == [partner.id]


async def test_partner_deleted(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    me, partner = await user_with_profile(session), await user_with_profile(session)
    await matched(session, me, partner)

    assert (await client.delete(f"/users/{partner.id}")).status_code == 204

    assert (await matches_of(client, me))["total"] == 0


# Who liked me


async def likers_of(client: httpx.AsyncClient, user: User) -> httpx.Response:
    return await client.get("/likers", headers=headers(user))


async def test_who_liked_me_on_the_free_plan(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    me = await create_user(session)

    response = await likers_of(client, me)

    assert response.status_code == 403
    assert response.json()["code"] == "PREMIUM_REQUIRED"


async def test_who_liked_me_order(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    me = await create_user(session)
    await create_subscription(session, me)
    ages = {"old like": 4, "new like": 1, "old superlike": 3, "new superlike": 2}
    ids = {}
    for name, days_ago in ages.items():
        liker = await user_with_profile(session)
        like = await create_reaction(session, liker, me, is_super="superlike" in name)
        await session.execute(
            update(Reaction)
            .where(Reaction.id == like.id)
            .values(created_at=func.now() - timedelta(days=days_ago))
        )
        ids[liker.id] = name
    await session.commit()

    items = (await likers_of(client, me)).json()["items"]

    assert [ids[item["user"]["id"]] for item in items] == [
        "new superlike",
        "old superlike",
        "new like",
        "old like",
    ]


async def test_reacted_likers_leave_the_list(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    me = await create_user(session)
    await create_subscription(session, me)
    liker = await user_with_profile(session)
    await create_reaction(session, liker, me)

    await react(client, me, liker.id, action="dislike")

    assert (await likers_of(client, me)).json()["items"] == []


async def test_banned_and_hidden_likers(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    me = await create_user(session)
    await create_subscription(session, me)
    banned = await user_with_profile(session)
    hidden = await create_user(session)
    await create_profile(session, hidden, is_visible=False)
    for liker in (banned, hidden):
        await create_reaction(session, liker, me)
    await create_ban(session, banned)

    body = (await likers_of(client, me)).json()

    assert [item["user"]["id"] for item in body["items"]] == [hidden.id]
    assert body["total"] == 1


async def test_likers_show_no_message_and_no_contact(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    me = await create_user(session)
    await create_subscription(session, me)
    liker = await user_with_profile(session, username="secret_handle")
    await create_reaction(session, liker, me, message="Secret words")

    response = await likers_of(client, me)

    [item] = response.json()["items"]
    assert set(item) == {"user", "is_super"}
    assert "Secret words" not in response.text
    assert "secret_handle" not in response.text


async def test_like_back_from_the_list(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    me = await user_with_profile(session)
    await create_subscription(session, me)
    liker = await user_with_profile(session)
    await create_reaction(session, liker, me)

    response = await react(client, me, liker.id)

    assert response.json()["match"]["user"]["id"] == liker.id
