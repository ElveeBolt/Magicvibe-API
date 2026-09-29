from typing import TYPE_CHECKING, Any

from ..core.exceptions import ConflictError, ErrorCode
from ..user.schemas.user import UserPublicSchema
from ..user.utils import birth_date_bounds

if TYPE_CHECKING:
    from ..uow import UnitOfWork
    from ..user.schemas.user import UserReadSchema
    from ..user.schemas.user_preference import UserPreferenceReadSchema
    from ..user.schemas.user_profile import UserProfileReadSchema


class DiscoveryService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_next_candidate(
        self, viewer: UserReadSchema
    ) -> UserPublicSchema | None:
        """Next profile to show to `viewer`, or `None` when nobody is left;
        running out is a normal outcome.

        Browsing needs a profile and preferences of one's own: the fit is
        checked in both directions.
        """
        if viewer.profile is None:
            raise ConflictError(
                "Complete your profile to start browsing",
                code=ErrorCode.PROFILE_REQUIRED,
            )
        if viewer.preference is None:
            raise ConflictError(
                "Set your preferences to start browsing",
                code=ErrorCode.PREFERENCES_REQUIRED,
            )

        filters = self._to_filters(viewer.profile, viewer.preference)

        async with self.uow:
            candidate = await self.uow.discovery.get_next_candidate(viewer.id, filters)

            if candidate is None:
                return None

            return UserPublicSchema.model_validate(candidate)

    @staticmethod
    def _to_filters(
        profile: UserProfileReadSchema, preference: UserPreferenceReadSchema
    ) -> dict[str, Any]:
        """Both sides of the fit, in the terms the query works in.

        `gender`, `city_id`, `dating_goal` and `*_birth_date` are what the
        viewer is looking for (`None` = any): the stored age range becomes a
        birth-date window, recomputed on every request because "18-25" means
        something different on every date. `viewer_*` is what the viewer offers
        the other side.
        """
        earliest, latest = birth_date_bounds(preference.min_age, preference.max_age)

        return {
            "gender": preference.gender,
            "city_id": preference.city_id,
            "dating_goal": preference.dating_goal,
            "earliest_birth_date": earliest,
            "latest_birth_date": latest,
            "viewer_age": profile.age,
            "viewer_gender": profile.gender,
            "viewer_city_id": profile.city_id,
            "viewer_dating_goal": profile.dating_goal,
        }
