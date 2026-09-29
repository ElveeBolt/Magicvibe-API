from datetime import UTC, datetime

from ..core.database.alchemy.repository import AlchemyRepository
from .models import Ban


class BanRepository(AlchemyRepository[Ban, int]):
    model = Ban

    async def get_active(self, user_id: int) -> Ban | None:
        """A ban is active until it is lifted; it has no end date."""
        stmt = self._get_base_stmt().where(
            Ban.user_id == user_id, Ban.lifted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def lift(self, ban: Ban, lift_comment: str | None) -> Ban:
        ban.lifted_at = datetime.now(UTC)
        ban.lift_comment = lift_comment

        await self._session.flush()
        await self._session.refresh(ban)
        return ban
