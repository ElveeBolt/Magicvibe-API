from typing import TYPE_CHECKING, Any

from ..core.exceptions import BadRequestError
from ..user.constants import MAX_PROFILE_AGE, MIN_PROFILE_AGE
from ..user.schemas.user import UserPublicSchema
from ..user.utils import birth_date_bounds
from .schemas.candidate import NextCandidateSchema

if TYPE_CHECKING:
    from ..uow import UnitOfWork
    from ..user.schemas.user import UserReadSchema


class DiscoveryService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_next_candidate(self, viewer: UserReadSchema) -> NextCandidateSchema:
        """Next profile to show to `viewer`; running out is a normal outcome.

        Browsing needs a profile of one's own: the search is mutual, and without
        a gender and an age there is nothing to offer the other side.
        """
        if viewer.profile is None:
            raise BadRequestError("Complete your profile to start browsing")

        filters = self._to_filters(viewer)

        async with self.uow:
            candidate = await self.uow.discovery.get_next_candidate(viewer.id, filters)

            return NextCandidateSchema(
                candidate=(
                    UserPublicSchema.model_validate(candidate)
                    if candidate is not None
                    else None
                )
            )

    @staticmethod
    def _to_filters(viewer: UserReadSchema) -> dict[str, Any]:
        """Both sides of the search, in the terms the query works in.

        `gender` / `*_birth_date` are what the viewer is looking for: the stored
        age range becomes a birth-date window, recomputed on every request
        because "18-25" means something different on every date it is evaluated.
        `viewer_*` is what the viewer offers the other side.

        A user with no criteria of their own is read as having the default ones,
        which is what the columns themselves default to.
        """
        if viewer.profile is None:
            raise ValueError("The viewer must have a profile")

        preference = viewer.preference
        earliest, latest = birth_date_bounds(
            preference.min_age if preference else MIN_PROFILE_AGE,
            preference.max_age if preference else MAX_PROFILE_AGE,
        )

        return {
            "gender": preference.gender if preference else None,
            "earliest_birth_date": earliest,
            "latest_birth_date": latest,
            "viewer_age": viewer.profile.age,
            "viewer_gender": viewer.profile.gender,
        }
