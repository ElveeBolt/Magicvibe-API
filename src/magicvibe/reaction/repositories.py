from typing import TYPE_CHECKING, Any

from sqlalchemy import ColumnElement, and_, case, func, or_, select
from sqlalchemy.dialects.postgresql import insert

from ..core.database.alchemy.repository import AlchemyRepository
from ..user.enums import UserStatus
from ..user.models import User
from .enums import ReactionAction
from .models import Match, Reaction

if TYPE_CHECKING:
    from collections.abc import Sequence

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

    async def get_like(self, from_user_id: int, to_user_id: int) -> Reaction | None:
        """The like (or superlike) `from_user_id` gave `to_user_id`, if any."""
        stmt = self._get_base_stmt().where(
            Reaction.from_user_id == from_user_id,
            Reaction.to_user_id == to_user_id,
            Reaction.action == ReactionAction.LIKE,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class MatchRepository(AlchemyRepository[Match, int]):
    model = Match

    async def create_pair(self, first_user_id: int, second_user_id: int) -> Match:
        """Stores the pair in its fixed order: the smaller ID first."""
        return await self.create(
            {
                "user_a_id": min(first_user_id, second_user_id),
                "user_b_id": max(first_user_id, second_user_id),
            }
        )

    async def get_for_user(
        self, user_id: int, descending: bool, limit: int, offset: int
    ) -> Sequence[Row[tuple[Match, User, Reaction]]]:
        """The user's matches with the partner and the partner's like to the
        user. Matches with a banned partner are left out while the ban lasts."""
        stmt = (
            self._for_user(select(Match, User, Reaction), user_id)
            .order_by(Match.created_at.desc() if descending else Match.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return result.unique().all()

    async def count_for_user(self, user_id: int) -> int:
        stmt = self._for_user(select(func.count(Match.id)), user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    def _for_user[T: Any](stmt: T, user_id: int) -> T:
        partner_id = case(
            (Match.user_a_id == user_id, Match.user_b_id), else_=Match.user_a_id
        )
        return (
            stmt.select_from(Match)
            .join(User, User.id == partner_id)
            .join(Reaction, MatchRepository._partners_like(user_id))
            .where(
                or_(Match.user_a_id == user_id, Match.user_b_id == user_id),
                User.status == UserStatus.ACTIVE,
            )
        )

    @staticmethod
    def _partners_like(user_id: int) -> ColumnElement[bool]:
        return and_(
            Reaction.from_user_id == User.id,
            Reaction.to_user_id == user_id,
            Reaction.action == ReactionAction.LIKE,
        )
