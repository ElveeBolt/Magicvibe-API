from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import aliased

from ..core.database.alchemy.repository import AlchemyRepository
from ..user.models import User
from .enums import SwipeAction
from .models import Swipe

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from sqlalchemy import Row


class SwipeRepository(AlchemyRepository[Swipe, int]):
    model = Swipe

    async def create_if_not_exists(self, data: dict[str, Any]) -> Swipe | None:
        stmt = (
            insert(Swipe)
            .values(**data)
            .on_conflict_do_nothing(constraint="uq_swipe_pair")
            .returning(Swipe)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_matches(
        self, user_id: int, descending: bool, limit: int, offset: int
    ) -> Sequence[Row[tuple[User, datetime]]]:
        """Partners who liked `user_id` back, with the moment the like became mutual."""
        theirs = aliased(Swipe, name="theirs")
        matched_at = func.greatest(Swipe.created_at, theirs.created_at).label(
            "matched_at"
        )
        stmt = (
            select(User, matched_at)
            .select_from(Swipe)
            .join(theirs, self._is_reverse_like(theirs))
            .join(User, User.id == Swipe.to_user_id)
            .where(Swipe.from_user_id == user_id, Swipe.action == SwipeAction.LIKE)
            .order_by(matched_at.desc() if descending else matched_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return result.all()

    async def count_matches(self, user_id: int) -> int:
        theirs = aliased(Swipe, name="theirs")
        stmt = (
            select(func.count())
            .select_from(Swipe)
            .join(theirs, self._is_reverse_like(theirs))
            .where(Swipe.from_user_id == user_id, Swipe.action == SwipeAction.LIKE)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    def _is_reverse_like(theirs: type[Swipe]):
        """Join condition: `theirs` is a like from the target back to the swiper."""
        return (
            (theirs.from_user_id == Swipe.to_user_id)
            & (theirs.to_user_id == Swipe.from_user_id)
            & (theirs.action == SwipeAction.LIKE)
        )
