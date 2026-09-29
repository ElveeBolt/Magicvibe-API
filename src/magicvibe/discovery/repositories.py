from typing import Any

from sqlalchemy import ColumnElement, and_, func, or_, select
from sqlalchemy.orm import contains_eager

from ..core.database.alchemy.repository import AlchemyRepository
from ..reaction.models import Reaction
from ..user.enums import UserStatus
from ..user.models import User, UserPreference, UserProfile


class DiscoveryRepository(AlchemyRepository[User, int]):
    model = User

    async def get_next_candidate(
        self, user_id: int, filters: dict[str, Any]
    ) -> User | None:
        """A random candidate for `user_id`, or `None`. The inner joins leave
        out users without a profile or without preferences: the fit in their
        direction cannot be checked."""
        stmt = (
            select(User)
            .join(User.profile)
            .join(User.preference)
            .options(contains_eager(User.profile), contains_eager(User.preference))
            .where(
                self._eligible(user_id),
                self._wanted(filters),
                self._accepted_by(filters),
            )
            .order_by(func.random())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _eligible(user_id: int) -> ColumnElement[bool]:
        """Whom the platform may show at all: an active, visible profile that is
        neither the viewer nor someone they already reacted to."""
        reacted = select(Reaction.to_user_id).where(Reaction.from_user_id == user_id)
        return and_(
            User.status == UserStatus.ACTIVE,
            UserProfile.is_visible,
            User.id != user_id,
            User.id.not_in(reacted),
        )

    @staticmethod
    def _wanted(filters: dict[str, Any]) -> ColumnElement[bool]:
        """The viewer's preferences applied to the candidate; a criterion the
        viewer left as "any" (`None`) does not narrow anything."""
        conditions = [
            UserProfile.birth_date > filters["earliest_birth_date"],
            UserProfile.birth_date <= filters["latest_birth_date"],
        ]
        for column, key in (
            (UserProfile.gender, "gender"),
            (UserProfile.city_id, "city_id"),
            (UserProfile.dating_goal, "dating_goal"),
        ):
            if (value := filters[key]) is not None:
                conditions.append(column == value)

        return and_(*conditions)

    @staticmethod
    def _accepted_by(filters: dict[str, Any]) -> ColumnElement[bool]:
        """The candidate's preferences applied to the viewer; `NULL` in a
        candidate's criterion means "any"."""
        return and_(
            UserPreference.min_age <= filters["viewer_age"],
            UserPreference.max_age >= filters["viewer_age"],
            *(
                or_(column.is_(None), column == filters[key])
                for column, key in (
                    (UserPreference.gender, "viewer_gender"),
                    (UserPreference.city_id, "viewer_city_id"),
                    (UserPreference.dating_goal, "viewer_dating_goal"),
                )
            ),
        )
