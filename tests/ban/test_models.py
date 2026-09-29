from typing import TYPE_CHECKING

import pytest
from sqlalchemy.exc import IntegrityError

from magicvibe.exceptions import constraint_name
from tests.factories import create_ban, create_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def test_one_active_ban_per_user(session: AsyncSession) -> None:
    user = await create_user(session)
    await create_ban(session, user)

    with pytest.raises(IntegrityError) as error:
        await create_ban(session, user)

    assert constraint_name(error.value) == "ix_bans_user_id"
