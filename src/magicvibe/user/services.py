from typing import TYPE_CHECKING

from ..ban.schemas.ban import BanReadSchema
from ..core.database.alchemy.service import AlchemyService
from ..core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    GoneError,
    NotFoundError,
)
from .enums import UserStatus
from .schemas.user import (
    UserCreateSchema,
    UserFilterSchema,
    UserReadSchema,
    UserUpdateSchema,
)
from .schemas.user_preference import (
    UserPreferenceCreateSchema,
    UserPreferenceReadSchema,
    UserPreferenceUpdateSchema,
)
from .schemas.user_profile import (
    UserProfileCreateSchema,
    UserProfileReadSchema,
    UserProfileUpdateSchema,
)
from .schemas.user_telegram import UserTelegramReadSchema, UserTelegramUpdateSchema
from .schemas.validators import validate_age_bounds

if TYPE_CHECKING:
    from ..uow import UnitOfWork
    from .models import User, UserPreference, UserProfile, UserTelegram
    from .repositories import UserRepository


class UserService(
    AlchemyService[
        UserCreateSchema, UserUpdateSchema, UserReadSchema, UserFilterSchema, int
    ]
):
    schema = UserReadSchema
    uow: UnitOfWork

    @property
    def repository(self) -> UserRepository:  # type: ignore[override]
        return self.uow.user

    async def get_by_telegram_id(self, telegram_id: int) -> UserReadSchema:
        async with self.uow:
            user = await self.repository.get_by_telegram_id(telegram_id)

            if user is None:
                raise NotFoundError("User not found")

            return self._to_schema(user)

    async def upsert(self, data: UserCreateSchema) -> tuple[UserReadSchema, bool]:
        async with self.uow:
            user, is_created = await self.repository.upsert_by_telegram_id(
                data.telegram.model_dump()
            )

            if user.status is UserStatus.DELETED:
                user = await self.repository.restore(user)

            return self._to_schema(user), is_created

    async def get_acting_user(self, telegram_id: int) -> UserReadSchema:
        async with self.uow:
            user = await self.repository.get_by_telegram_id(telegram_id)

            if user is None:
                raise NotFoundError("User not found")

            if user.status is UserStatus.DELETED:
                raise GoneError("Account is deleted")

            if user.status is UserStatus.BANNED:
                ban = await self.uow.ban.get_active(user.id)

                if ban is None:
                    user.status = UserStatus.ACTIVE
                else:
                    raise ForbiddenError(
                        "Account is banned",
                        details={
                            "ban": BanReadSchema.model_validate(ban).model_dump(
                                mode="json"
                            )
                        },
                    )

            return self._to_schema(user)

    async def soft_delete(self, id_: int) -> None:
        async with self.uow:
            user = await self._get_or_raise(id_)

            if user.status is UserStatus.DELETED:
                raise ConflictError("Account is already deleted")

            if await self.uow.ban.get_active(user.id) is not None:
                raise ForbiddenError("A banned account cannot be deleted")

            await self.repository.soft_delete(user)

    async def restore(self, user_id: int) -> UserReadSchema:
        async with self.uow:
            user = await self._get_or_raise(user_id)

            if user.status is not UserStatus.DELETED:
                raise ConflictError("Account is not deleted")

            user = await self.repository.restore(user)
            return self._to_schema(user)

    async def get_profile(self, user_id: int) -> UserProfileReadSchema:
        async with self.uow:
            user = await self._get_or_raise(user_id)
            user_profile = self._profile_or_raise(user)
            return UserProfileReadSchema.model_validate(user_profile)

    async def set_profile(
        self, user_id: int, data: UserProfileCreateSchema
    ) -> UserProfileReadSchema:
        async with self.uow:
            user = await self._get_or_raise(user_id)
            user_profile = await self.repository.set_profile(user, data.model_dump())
            await self.repository.get_or_create_preference(user)
            return UserProfileReadSchema.model_validate(user_profile)

    async def update_profile(
        self, user_id: int, data: UserProfileUpdateSchema
    ) -> UserProfileReadSchema:
        async with self.uow:
            user = await self._get_or_raise(user_id)
            user_profile = self._profile_or_raise(user)
            user_profile = await self.repository.update_profile(
                user_profile, data.model_dump(exclude_unset=True)
            )
            return UserProfileReadSchema.model_validate(user_profile)

    async def get_preference(self, user_id: int) -> UserPreferenceReadSchema:
        async with self.uow:
            user = await self._get_or_raise(user_id)
            user_preference = self._preference_or_raise(user)
            return UserPreferenceReadSchema.model_validate(user_preference)

    async def set_preference(
        self, user_id: int, data: UserPreferenceCreateSchema
    ) -> UserPreferenceReadSchema:
        async with self.uow:
            user = await self._get_or_raise(user_id)
            user_preference = await self.repository.set_preference(
                user, data.model_dump()
            )
            return UserPreferenceReadSchema.model_validate(user_preference)

    async def update_preference(
        self, user_id: int, data: UserPreferenceUpdateSchema
    ) -> UserPreferenceReadSchema:
        async with self.uow:
            user = await self._get_or_raise(user_id)
            user_preference = self._preference_or_raise(user)
            update_data = data.model_dump(exclude_unset=True)

            # One bound may be updated on its own, so the range is only whole
            # once the stored values are merged in.
            try:
                validate_age_bounds(
                    update_data.get("min_age", user_preference.min_age),
                    update_data.get("max_age", user_preference.max_age),
                )
            except ValueError as exc:
                raise BadRequestError(str(exc)) from exc

            user_preference = await self.repository.update_preference(
                user_preference, update_data
            )
            return UserPreferenceReadSchema.model_validate(user_preference)

    async def get_telegram(self, user_id: int) -> UserTelegramReadSchema:
        async with self.uow:
            user = await self._get_or_raise(user_id)
            return UserTelegramReadSchema.model_validate(self._telegram_or_raise(user))

    async def update_telegram(
        self, user_id: int, data: UserTelegramUpdateSchema
    ) -> UserTelegramReadSchema:
        async with self.uow:
            user = await self._get_or_raise(user_id)
            telegram = self._telegram_or_raise(user)
            telegram = await self.repository.update_telegram(
                telegram, data.model_dump(exclude_unset=True)
            )
            return UserTelegramReadSchema.model_validate(telegram)

    async def _get_or_raise(self, id_: int) -> User:
        user = await self.repository.get(id_=id_)

        if user is None:
            raise NotFoundError("User not found")

        return user

    @staticmethod
    def _profile_or_raise(user: User) -> UserProfile:
        if user.profile is None:
            raise NotFoundError("Profile not found")

        return user.profile

    @staticmethod
    def _preference_or_raise(user: User) -> UserPreference:
        if user.preference is None:
            raise NotFoundError("Preferences not found")

        return user.preference

    @staticmethod
    def _telegram_or_raise(user: User) -> UserTelegram:
        if user.telegram is None:
            raise NotFoundError("Telegram account not found")

        return user.telegram
