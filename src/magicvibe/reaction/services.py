from typing import TYPE_CHECKING

from ..core.exceptions import (
    BadRequestError,
    ConflictError,
    ErrorCode,
    NotFoundError,
)
from ..core.schemas.base import PaginatedResponse
from .enums import ReactionAction
from .schemas.reaction import (
    MatchedUserSchema,
    MatchFilterSchema,
    MatchReadSchema,
    ReactionCreateSchema,
    ReactionFilterSchema,
    ReactionReadSchema,
    ReactionResultReadSchema,
)

if TYPE_CHECKING:
    from ..uow import UnitOfWork


class ReactionService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def create(
        self, user_id: int, data: ReactionCreateSchema
    ) -> ReactionResultReadSchema:
        """Record a reaction by `user_id` (already authenticated) and detect a match."""
        if user_id == data.to_user_id:
            raise BadRequestError(
                "A user cannot react to themselves", code=ErrorCode.SELF_ACTION
            )

        async with self.uow:
            target_user = await self.uow.user.get(id_=data.to_user_id)
            if target_user is None:
                raise NotFoundError("Target user not found")

            reaction = await self.uow.reaction.create_if_not_exists(
                {**data.model_dump(), "from_user_id": user_id}
            )
            if reaction is None:
                raise ConflictError(
                    "User already reacted to this profile",
                    code=ErrorCode.ALREADY_REACTED,
                )

            is_match = data.action == ReactionAction.LIKE and await self._liked_back(
                from_user_id=user_id, to_user_id=data.to_user_id
            )

            return ReactionResultReadSchema(
                reaction=ReactionReadSchema.model_validate(reaction),
                match=(
                    MatchReadSchema(
                        user=MatchedUserSchema.model_validate(target_user),
                        matched_at=reaction.created_at,
                    )
                    if is_match
                    else None
                ),
            )

    async def get_matches(
        self, user_id: int, filters: MatchFilterSchema
    ) -> PaginatedResponse[MatchReadSchema]:
        async with self.uow:
            total = await self.uow.reaction.count_matches(user_id)
            rows = await self.uow.reaction.get_matches(
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
        reverse_like = ReactionFilterSchema(
            from_user_id=to_user_id,
            to_user_id=from_user_id,
            action=ReactionAction.LIKE,
        )
        return await self.uow.reaction.exists_by(reverse_like.to_filter_dict())
