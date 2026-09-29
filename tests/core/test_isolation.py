from typing import TYPE_CHECKING

import pytest
from sqlalchemy import func, select

from magicvibe.user.models import User
from tests.factories import create_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

SHARED_TELEGRAM_ID = 42


# Both runs create the same Telegram ID, which is unique: the second run fails
# unless the first one was rolled back. Every run also starts from an empty
# table, which covers the truncation after concurrency tests too.
@pytest.mark.parametrize("run", [1, 2])
async def test_each_test_starts_from_an_empty_database(
    session: AsyncSession, run: int
) -> None:
    assert await session.scalar(select(func.count()).select_from(User)) == 0

    await create_user(session, telegram_id=SHARED_TELEGRAM_ID)

    assert await session.scalar(select(func.count()).select_from(User)) == 1
