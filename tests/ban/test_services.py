from typing import TYPE_CHECKING

import pytest

from magicvibe.ban.enums import BanReason
from magicvibe.ban.schemas.ban import BanCreateSchema, BanLiftSchema
from magicvibe.ban.services import BanService
from magicvibe.core.exceptions import ConflictError, ErrorCode
from magicvibe.user.enums import UserStatus
from magicvibe.user.services import UserService
from tests.factories import create_ban, create_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from magicvibe.uow import UnitOfWork


async def test_create_sets_the_user_banned(
    uow: UnitOfWork, session: AsyncSession
) -> None:
    user = await create_user(session)

    await BanService(uow).create(
        BanCreateSchema(user_id=user.id, reason=BanReason.SPAM)
    )

    assert (await UserService(uow).get(user.id)).status is UserStatus.BANNED


async def test_create_rejects_a_second_active_ban(
    uow: UnitOfWork, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_ban(session, user)

    with pytest.raises(ConflictError) as error:
        await BanService(uow).create(
            BanCreateSchema(user_id=user.id, reason=BanReason.SPAM)
        )

    assert error.value.code is ErrorCode.BAN_ALREADY_ACTIVE


async def test_lift_sets_the_user_active(
    uow: UnitOfWork, session: AsyncSession
) -> None:
    user = await create_user(session)
    ban = await create_ban(session, user)

    lifted = await BanService(uow).lift(ban.id, BanLiftSchema(lift_comment=None))

    assert lifted.lifted_at is not None
    assert (await UserService(uow).get(user.id)).status is UserStatus.ACTIVE
