from typing import Any

from sqlalchemy import func, select
from sqlalchemy import update as update_sql

from ..core.database.alchemy.models import Base
from ..core.database.alchemy.repository import AlchemyRepository
from .constants import LAST_SEEN_UPDATE_INTERVAL
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

    async def get_for_update(self, id_: int) -> User | None:
        """The user with their row locked until the transaction ends. Only
        `users` is locked: the joined relationships are outer joins, which
        PostgreSQL cannot lock."""
        stmt = self._get_base_stmt().where(User.id == id_).with_for_update(of=User)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def lock_telegram_id(self, telegram_id: int) -> None:
        """Serializes registrations of one Telegram account until the
        transaction ends, also when no row exists yet to lock."""
        await self._session.execute(select(func.pg_advisory_xact_lock(telegram_id)))

    async def create_with_telegram(self, data: dict[str, Any]) -> User:
        user = User(telegram=UserTelegram(**data))
        self._session.add(user)
        return await self._persist(user)

    async def touch_last_seen(self, user: User) -> None:
        """Sets `last_seen_at` to now when it is older than the interval."""
        stmt = (
            update_sql(User)
            .where(
                User.id == user.id,
                User.last_seen_at < func.now() - LAST_SEEN_UPDATE_INTERVAL,
            )
            .values(last_seen_at=func.now())
            .returning(User.id)
            .execution_options(synchronize_session=False)
        )
        result = await self._session.execute(stmt)

        if result.scalar_one_or_none() is not None:
            await self._session.refresh(user, ["last_seen_at", "updated_at"])

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
