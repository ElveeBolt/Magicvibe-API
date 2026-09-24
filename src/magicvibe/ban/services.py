from typing import TYPE_CHECKING

from ..core.database.alchemy.service import AlchemyService
from ..core.exceptions import ConflictError, NotFoundError
from ..user.enums import UserStatus
from .schemas.ban import (
    BanCreateSchema,
    BanFilterSchema,
    BanLiftSchema,
    BanReadSchema,
    BanUpdateSchema,
)

if TYPE_CHECKING:
    from ..uow import UnitOfWork
    from .models import Ban
    from .repositories import BanRepository


class BanService(
    AlchemyService[
        BanCreateSchema, BanUpdateSchema, BanReadSchema, BanFilterSchema, int
    ]
):
    schema = BanReadSchema
    uow: UnitOfWork

    @property
    def repository(self) -> BanRepository:  # type: ignore[override]
        return self.uow.ban

    async def create(self, data: BanCreateSchema) -> BanReadSchema:
        async with self.uow:
            user = await self.uow.user.get(id_=data.user_id)

            if user is None:
                raise NotFoundError("User not found")

            if await self.repository.has_unlifted(data.user_id):
                raise ConflictError("User already has an active ban; update it instead")

            ban = await self.repository.create(data.model_dump())
            user.status = UserStatus.BANNED

            return self._to_schema(ban)

    async def lift(self, ban_id: int, data: BanLiftSchema) -> BanReadSchema:
        async with self.uow:
            ban = await self._get_or_raise(ban_id)

            if ban.lifted_at is not None:
                raise ConflictError("Ban is already lifted")

            ban = await self.repository.lift(ban, data.lift_comment)
            await self._unban_user(ban.user_id)

            return self._to_schema(ban)

    async def _unban_user(self, user_id: int) -> None:
        user = await self.uow.user.get(id_=user_id)

        if user is not None and user.status is UserStatus.BANNED:
            user.status = UserStatus.ACTIVE

    async def _get_or_raise(self, ban_id: int) -> Ban:
        ban = await self.repository.get(id_=ban_id)

        if ban is None:
            raise NotFoundError("Ban not found")

        return ban
