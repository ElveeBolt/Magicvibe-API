from typing import TYPE_CHECKING

import pytest

from magicvibe.ban.enums import BanReason
from magicvibe.ban.models import Ban
from magicvibe.core.exceptions import ErrorCode, ForbiddenError, NotFoundError
from magicvibe.user.schemas.user import UserCreateSchema
from magicvibe.user.services import UserService, user_banned_error
from tests.factories import create_ban, create_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from magicvibe.uow import UnitOfWork


def test_user_banned_error_carries_only_reason_and_comment() -> None:
    ban = Ban(id=7, user_id=1, reason=BanReason.SPAM, comment="Ads", lift_comment="x")

    error = user_banned_error(ban)

    assert error.code is ErrorCode.USER_BANNED
    assert error.status_code == 403
    assert error.extra == {"ban": {"reason": BanReason.SPAM, "comment": "Ads"}}


async def test_upsert_of_a_banned_user_writes_nothing(
    uow: UnitOfWork, session: AsyncSession
) -> None:
    user = await create_user(session, telegram_id=6001, first_name="Old")
    await create_ban(session, user)
    data = UserCreateSchema.model_validate(
        {"telegram": {"telegram_id": 6001, "first_name": "New"}}
    )

    with pytest.raises(ForbiddenError) as error:
        await UserService(uow).upsert(data)

    assert error.value.code is ErrorCode.USER_BANNED
    telegram = await UserService(uow).get_telegram(user.id)
    assert telegram.first_name == "Old"


async def test_upsert_creates_then_refreshes(uow: UnitOfWork) -> None:
    service = UserService(uow)
    data = {"telegram": {"telegram_id": 6002, "first_name": "Ann"}}

    created, is_created = await service.upsert(UserCreateSchema.model_validate(data))
    data["telegram"]["first_name"] = "Anna"
    refreshed, is_created_again = await service.upsert(
        UserCreateSchema.model_validate(data)
    )

    assert (is_created, is_created_again) == (True, False)
    assert refreshed.id == created.id
    assert refreshed.telegram is not None
    assert refreshed.telegram.first_name == "Anna"


async def test_delete_of_a_banned_user_is_refused(
    uow: UnitOfWork, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_ban(session, user)

    with pytest.raises(ForbiddenError) as error:
        await UserService(uow).delete(user.id)

    assert error.value.code is ErrorCode.USER_BANNED
    assert await UserService(uow).exists(user.id)


async def test_delete_of_an_unknown_user(uow: UnitOfWork) -> None:
    with pytest.raises(NotFoundError) as error:
        await UserService(uow).delete(999_999)

    assert error.value.code is ErrorCode.NOT_FOUND
