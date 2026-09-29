from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import aliased

from ..core.database.alchemy.repository import AlchemyRepository
from ..user.models import User
from .enums import ReactionAction
from .models import Reaction

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from sqlalchemy import Row


class ReactionRepository(AlchemyRepository[Reaction, int]):
    model = Reaction

    async def create_if_not_exists(self, data: dict[str, Any]) -> Reaction | None:
        stmt = (
            insert(Reaction)
            .values(**data)
            .on_conflict_do_nothing(constraint="uq_reaction_pair")
            .returning(Reaction)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_matches(
        self, user_id: int, descending: bool, limit: int, offset: int
    ) -> Sequence[Row[tuple[User, datetime]]]:
        """Partners who liked `user_id` back, with the moment the like became mutual."""
        theirs = aliased(Reaction, name="theirs")
        matched_at = func.greatest(Reaction.created_at, theirs.created_at).label(
            "matched_at"
        )
        stmt = (
            select(User, matched_at)
            .select_from(Reaction)
            .join(theirs, self._is_reverse_like(theirs))
            .join(User, User.id == Reaction.to_user_id)
            .where(
                Reaction.from_user_id == user_id, Reaction.action == ReactionAction.LIKE
            )
            .order_by(matched_at.desc() if descending else matched_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return result.all()

    async def count_matches(self, user_id: int) -> int:
        theirs = aliased(Reaction, name="theirs")
        stmt = (
            select(func.count())
            .select_from(Reaction)
            .join(theirs, self._is_reverse_like(theirs))
            .where(
                Reaction.from_user_id == user_id, Reaction.action == ReactionAction.LIKE
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    def _is_reverse_like(theirs: type[Reaction]):
        """Join condition: `theirs` is a like from the target back to the reactionr."""
        return (
            (theirs.from_user_id == Reaction.to_user_id)
            & (theirs.to_user_id == Reaction.from_user_id)
            & (theirs.action == ReactionAction.LIKE)
        )
