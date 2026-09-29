from typing import TYPE_CHECKING

import pytest

from magicvibe.core.exceptions import ConflictError, ErrorCode
from magicvibe.discovery.services import DiscoveryService
from magicvibe.user.services import UserService
from tests.factories import create_profile, create_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from magicvibe.uow import UnitOfWork


async def test_browsing_without_a_profile(
    uow: UnitOfWork, session: AsyncSession
) -> None:
    viewer = await UserService(uow).get((await create_user(session)).id)

    with pytest.raises(ConflictError) as error:
        await DiscoveryService(uow).get_next_candidate(viewer=viewer)

    assert error.value.code is ErrorCode.PROFILE_REQUIRED


async def test_browsing_without_preferences(
    uow: UnitOfWork, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_profile(session, user)
    viewer = await UserService(uow).get(user.id)

    with pytest.raises(ConflictError) as error:
        await DiscoveryService(uow).get_next_candidate(viewer=viewer)

    assert error.value.code is ErrorCode.PREFERENCES_REQUIRED
