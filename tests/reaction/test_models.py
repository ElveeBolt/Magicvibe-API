from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy.exc import IntegrityError

from magicvibe.exceptions import constraint_name
from magicvibe.reaction.enums import ReactionAction
from magicvibe.reaction.models import Match
from tests.factories import create_match, create_reaction, create_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def test_reaction_pair_is_unique(session: AsyncSession) -> None:
    viewer = await create_user(session)
    target = await create_user(session)
    await create_reaction(session, viewer, target)

    with pytest.raises(IntegrityError) as error:
        await create_reaction(session, viewer, target)

    assert constraint_name(error.value) == "uq_reaction_pair"


@pytest.mark.parametrize(
    ("fields", "name"),
    [
        ({"message": ""}, "ck_reactions_message_not_empty"),
        (
            {"action": ReactionAction.DISLIKE, "is_super": True},
            "ck_reactions_super_only_on_like",
        ),
        (
            {"action": ReactionAction.DISLIKE, "message": "x"},
            "ck_reactions_message_only_on_like",
        ),
    ],
)
async def test_reaction_checks(
    session: AsyncSession, fields: dict[str, Any], name: str
) -> None:
    viewer, target = await create_user(session), await create_user(session)

    with pytest.raises(IntegrityError) as error:
        await create_reaction(session, viewer, target, **fields)

    assert constraint_name(error.value) == name


async def test_no_reaction_to_oneself(session: AsyncSession) -> None:
    user = await create_user(session)

    with pytest.raises(IntegrityError) as error:
        await create_reaction(session, user, user)

    assert constraint_name(error.value) == "ck_reactions_not_self"


async def test_match_pair_is_ordered(session: AsyncSession) -> None:
    a, b = await create_user(session), await create_user(session)
    session.add(Match(user_a_id=max(a.id, b.id), user_b_id=min(a.id, b.id)))

    with pytest.raises(IntegrityError) as error:
        await session.flush()

    assert constraint_name(error.value) == "ck_matches_ordered_pair"


async def test_match_pair_is_unique(session: AsyncSession) -> None:
    a, b = await create_user(session), await create_user(session)
    await create_match(session, a, b)

    with pytest.raises(IntegrityError) as error:
        await create_match(session, b, a)

    assert constraint_name(error.value) == "uq_match_pair"
