from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select

from ..core.database.alchemy.models import Base
from ..core.database.alchemy.repository import AlchemyRepository
from .enums import UserStatus
from .models import User, UserPreference, UserProfile, UserTelegram


class UserRepository(AlchemyRepository[User, int]):
    model = User

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = self._get_base_stmt().where(
            User.id.in_(
                select(UserTelegram.user_id).where(
                    UserTelegram.telegram_id == telegram_id
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_by_telegram_id(self, data: dict[str, Any]) -> tuple[User, bool]:
        telegram_id = data["telegram_id"]
        await self._session.execute(select(func.pg_advisory_xact_lock(telegram_id)))

        user = await self.get_by_telegram_id(telegram_id)

        if user is not None:
            await self.set_telegram(user, data)
            return user, False

        user = User(telegram=UserTelegram(**data))
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)

        return user, True

    async def soft_delete(self, user: User) -> User:
        user.status = UserStatus.DELETED
        user.deleted_at = datetime.now(UTC)
        return await self._persist(user)

    async def restore(self, user: User) -> User:
        user.status = UserStatus.ACTIVE
        user.deleted_at = None

        return await self._persist(user)

    async def set_profile(self, user: User, data: dict[str, Any]) -> UserProfile:
        profile = user.profile

        if profile is None:
            profile = UserProfile(**data)
            user.profile = profile
            return await self._persist(profile)

        return await self.update_profile(profile, data)

    async def update_profile(
        self, profile: UserProfile, data: dict[str, Any]
    ) -> UserProfile:
        return await self._update(profile, data)

    async def get_or_create_preference(self, user: User) -> UserPreference:
        if user.preference is not None:
            return user.preference

        preference = UserPreference()
        user.preference = preference
        return await self._persist(preference)

    async def set_preference(self, user: User, data: dict[str, Any]) -> UserPreference:
        preference = user.preference

        if preference is None:
            preference = UserPreference(**data)
            user.preference = preference
            return await self._persist(preference)

        return await self.update_preference(preference, data)

    async def update_preference(
        self, preference: UserPreference, data: dict[str, Any]
    ) -> UserPreference:
        return await self._update(preference, data)

    async def set_telegram(self, user: User, data: dict[str, Any]) -> UserTelegram:
        telegram = user.telegram

        if telegram is None:
            telegram = UserTelegram(**data)
            user.telegram = telegram
            return await self._persist(telegram)

        return await self.update_telegram(telegram, data)

    async def update_telegram(
        self, telegram: UserTelegram, data: dict[str, Any]
    ) -> UserTelegram:
        return await self._update(telegram, data)

    async def _update[EntityType: Base](
        self, entity: EntityType, data: dict[str, Any]
    ) -> EntityType:
        for field, value in data.items():
            setattr(entity, field, value)

        return await self._persist(entity)

    async def _persist[EntityType: Base](self, entity: EntityType) -> EntityType:
        await self._session.flush()
        await self._session.refresh(entity)
        return entity
