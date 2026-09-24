from typing import TYPE_CHECKING

from ..core.exceptions import BadRequestError, ConflictError, NotFoundError
from ..core.schemas.base import PaginatedResponse
from .enums import SwipeAction
from .schemas.swipe import (
    MatchedUserSchema,
    MatchFilterSchema,
    MatchReadSchema,
    SwipeCreateSchema,
    SwipeFilterSchema,
    SwipeReadSchema,
    SwipeResultReadSchema,
)

if TYPE_CHECKING:
    from ..uow import UnitOfWork


class SwipeService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def create(
        self, user_id: int, data: SwipeCreateSchema
    ) -> SwipeResultReadSchema:
        """Record a swipe by `user_id` (already authenticated) and detect a match."""
        if user_id == data.to_user_id:
            raise BadRequestError("A user cannot swipe themselves")

        async with self.uow:
            target_user = await self.uow.user.get(id_=data.to_user_id)
            if target_user is None:
                raise NotFoundError("Target user not found")

            swipe = await self.uow.swipe.create_if_not_exists(
                {**data.model_dump(), "from_user_id": user_id}
            )
            if swipe is None:
                raise ConflictError("User already swiped this profile")

            is_match = data.action == SwipeAction.LIKE and await self._liked_back(
                from_user_id=user_id, to_user_id=data.to_user_id
            )

            return SwipeResultReadSchema(
                swipe=SwipeReadSchema.model_validate(swipe),
                match=(
                    MatchReadSchema(
                        user=MatchedUserSchema.model_validate(target_user),
                        matched_at=swipe.created_at,
                    )
                    if is_match
                    else None
                ),
            )

    async def get_matches(
        self, user_id: int, filters: MatchFilterSchema
    ) -> PaginatedResponse[MatchReadSchema]:
        async with self.uow:
            total = await self.uow.swipe.count_matches(user_id)
            rows = await self.uow.swipe.get_matches(
                user_id=user_id,
                descending=filters.descending,
                limit=filters.page_size,
                offset=filters.offset,
            )
            return PaginatedResponse.build(
                items=[
                    MatchReadSchema(
                        user=MatchedUserSchema.model_validate(user),
                        matched_at=matched_at,
                    )
                    for user, matched_at in rows
                ],
                total=total,
                filters=filters,
            )

    async def _liked_back(self, from_user_id: int, to_user_id: int) -> bool:
        reverse_like = SwipeFilterSchema(
            from_user_id=to_user_id,
            to_user_id=from_user_id,
            action=SwipeAction.LIKE,
        )
        return await self.uow.swipe.exists_by(reverse_like.to_filter_dict())
