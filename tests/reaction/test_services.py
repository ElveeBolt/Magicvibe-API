from typing import TYPE_CHECKING

from magicvibe.reaction.enums import ReactionAction
from magicvibe.reaction.schemas.reaction import (
    MatchFilterSchema,
    ReactionCreateSchema,
)
from magicvibe.reaction.services import ReactionService
from tests.factories import create_profile, create_reaction, create_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from magicvibe.uow import UnitOfWork


async def test_mutual_like_creates_one_match_for_both(
    uow: UnitOfWork, session: AsyncSession
) -> None:
    a, b = await create_user(session), await create_user(session)
    await create_profile(session, a)
    await create_profile(session, b)
    await create_reaction(session, a, b)
    service = ReactionService(uow)

    result = await service.create(
        b.id, ReactionCreateSchema(to_user_id=a.id, action=ReactionAction.LIKE)
    )
    a_matches = await service.get_matches(a.id, MatchFilterSchema())
    b_matches = await service.get_matches(b.id, MatchFilterSchema())

    assert result.match is not None
    assert [m.user.id for m in a_matches.items] == [b.id]
    assert [m.user.id for m in b_matches.items] == [a.id]


async def test_one_way_like_is_not_a_match(
    uow: UnitOfWork, session: AsyncSession
) -> None:
    a, b = await create_user(session), await create_user(session)
    service = ReactionService(uow)

    result = await service.create(
        a.id, ReactionCreateSchema(to_user_id=b.id, action=ReactionAction.LIKE)
    )

    assert result.match is None
    assert (await service.get_matches(a.id, MatchFilterSchema())).total == 0
