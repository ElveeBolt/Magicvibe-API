from typing import Any

from sqlalchemy import ColumnElement, and_, exists, func, or_, select
from sqlalchemy.orm import contains_eager

from ..core.database.alchemy.repository import AlchemyRepository
from ..swipe.enums import SwipeAction
from ..swipe.models import Swipe
from ..user.enums import UserStatus
from ..user.models import User, UserPreference, UserProfile


class DiscoveryRepository(AlchemyRepository[User, int]):
    model = User

    async def get_next_candidate(
        self, user_id: int, filters: dict[str, Any]
    ) -> User | None:
        stmt = (
            select(User)
            .join(User.profile)
            .options(contains_eager(User.profile))
            .where(
                self._eligible(user_id),
                self._wanted(filters),
                self._accepted_by(filters),
            )
            .order_by(*self._ranking(user_id))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _eligible(user_id: int) -> ColumnElement[bool]:
        """Whom the platform may show at all: an active, visible profile that is
        neither the viewer nor someone they already swiped."""
        swiped = select(Swipe.to_user_id).where(Swipe.from_user_id == user_id)
        return and_(
            User.status == UserStatus.ACTIVE,
            UserProfile.is_visible,
            User.id != user_id,
            User.id.not_in(swiped),
        )

    @staticmethod
    def _wanted(filters: dict[str, Any]) -> ColumnElement[bool]:
        """Narrowing the viewer asked for: the age window always applies, gender
        only when they picked one."""
        conditions = [
            UserProfile.birth_date > filters["earliest_birth_date"],
            UserProfile.birth_date <= filters["latest_birth_date"],
        ]

        if (gender := filters.get("gender")) is not None:
            conditions.append(UserProfile.gender == gender)

        return and_(*conditions)

    @staticmethod
    def _accepted_by(filters: dict[str, Any]) -> ColumnElement[bool]:
        """Candidates whose own criteria do not rule the viewer out.

        Phrased as "no preference of theirs rejects me" rather than "their
        preference accepts me", so a candidate who never set any criteria passes
        without a special case, exactly like an unrestricted one.
        """
        return ~exists().where(
            UserPreference.user_id == User.id,
            or_(
                UserPreference.min_age > filters["viewer_age"],
                UserPreference.max_age < filters["viewer_age"],
                and_(
                    UserPreference.gender.isnot(None),
                    UserPreference.gender != filters["viewer_gender"],
                ),
            ),
        )

    @staticmethod
    def _ranking(user_id: int) -> list[ColumnElement[Any]]:
        """Order within the eligible set."""
        superliked_me = exists().where(
            Swipe.from_user_id == User.id,
            Swipe.to_user_id == user_id,
            Swipe.action == SwipeAction.LIKE,
            Swipe.is_super,
        )
        return [superliked_me.desc(), func.random()]
