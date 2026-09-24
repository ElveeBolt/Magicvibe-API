from datetime import UTC, datetime

from sqlalchemy import or_

from ..core.database.alchemy.repository import AlchemyRepository
from .models import Ban


class BanRepository(AlchemyRepository[Ban, int]):
    model = Ban

    async def get_active(self, user_id: int) -> Ban | None:
        stmt = self._get_base_stmt().where(
            Ban.user_id == user_id,
            Ban.lifted_at.is_(None),
            or_(Ban.expires_at.is_(None), Ban.expires_at > datetime.now(UTC)),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_unlifted(self, user_id: int) -> bool:
        return await self.exists_by({"user_id": user_id, "lifted_at": None})

    async def lift(self, ban: Ban, lift_comment: str | None) -> Ban:
        ban.lifted_at = datetime.now(UTC)
        ban.lift_comment = lift_comment

        await self._session.flush()
        await self._session.refresh(ban)
        return ban
