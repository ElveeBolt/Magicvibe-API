from typing import TYPE_CHECKING

import pytest
from sqlalchemy.exc import IntegrityError

from magicvibe.exceptions import constraint_name
from tests.factories import create_reaction, create_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def test_reaction_pair_is_unique(session: AsyncSession) -> None:
    viewer = await create_user(session)
    target = await create_user(session)
    await create_reaction(session, viewer, target)

    with pytest.raises(IntegrityError) as error:
        await create_reaction(session, viewer, target)

    assert constraint_name(error.value) == "uq_reaction_pair"
