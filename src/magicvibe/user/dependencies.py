from typing import Annotated

from fastapi import Depends, Header

from ..dependencies import UOWDep
from .schemas.user import UserReadSchema
from .services import UserService

TELEGRAM_USER_ID_HEADER = "X-Telegram-User-Id"


async def get_user_service(uow: UOWDep) -> UserService:
    return UserService(uow)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


async def get_current_user(
    service: UserServiceDep,
    telegram_id: Annotated[int, Header(alias=TELEGRAM_USER_ID_HEADER)],
) -> UserReadSchema:
    """
    The acting user, resolved once per request from the bot-supplied header.

    The bot is a trusted client (see `require_service_token`), so the header
    is taken as-is; the user must already be registered via `POST /users`.
    """
    return await service.get_acting_user(telegram_id)


CurrentUserDep = Annotated[UserReadSchema, Depends(get_current_user)]
