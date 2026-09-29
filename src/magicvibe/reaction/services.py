from typing import TYPE_CHECKING

from ..core.exceptions import (
    BadRequestError,
    ConflictError,
    ErrorCode,
    NotFoundError,
)
from ..core.schemas.base import PaginatedResponse
from ..user.enums import UserStatus
from ..user.schemas.user import UserPublicSchema
from .enums import ReactionAction
from .schemas.reaction import (
    MatchContactSchema,
    MatchFilterSchema,
    MatchReadSchema,
    ReactionCreateSchema,
    ReactionReadSchema,
    ReactionResultReadSchema,
)

if TYPE_CHECKING:
    from datetime import datetime

    from ..uow import UnitOfWork
    from ..user.models import User
    from .models import Reaction


class ReactionService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def create(
        self, user_id: int, data: ReactionCreateSchema
    ) -> ReactionResultReadSchema:
        """Records a reaction of `user_id` (the acting user). A like that meets
        a like in the opposite direction creates the match in the same
        transaction; both users are locked first, so two opposite likes at the
        same time create exactly one match."""
        if user_id == data.to_user_id:
            raise BadRequestError(
                "A user cannot react to themselves", code=ErrorCode.SELF_ACTION
            )

        async with self.uow:
            statuses = await self.uow.user.lock_many([user_id, data.to_user_id])

            # Banned users are hidden from others, so they cannot be reacted to.
            if statuses.get(data.to_user_id, UserStatus.BANNED) is UserStatus.BANNED:
                raise NotFoundError("Target user not found")

            reaction = await self.uow.reaction.create_if_not_exists(
                {**data.model_dump(), "from_user_id": user_id}
            )
            if reaction is None:
                raise ConflictError(
                    "User already reacted to this profile",
                    code=ErrorCode.ALREADY_REACTED,
                )

            match = None
            if data.action is ReactionAction.LIKE:
                theirs = await self.uow.reaction.get_like(data.to_user_id, user_id)

                if theirs is not None:
                    created = await self.uow.match.create_pair(user_id, data.to_user_id)
                    partner = await self.uow.user.get(id_=data.to_user_id)
                    assert partner is not None  # locked above
                    match = self._to_match(partner, theirs, created.created_at)

            return ReactionResultReadSchema(
                reaction=ReactionReadSchema.model_validate(reaction), match=match
            )

    async def get_matches(
        self, user_id: int, filters: MatchFilterSchema
    ) -> PaginatedResponse[MatchReadSchema]:
        async with self.uow:
            total = await self.uow.match.count_for_user(user_id)
            rows = await self.uow.match.get_for_user(
                user_id=user_id,
                descending=filters.descending,
                limit=filters.page_size,
                offset=filters.offset,
            )
            return PaginatedResponse.build(
                items=[
                    self._to_match(partner, theirs, match.created_at)
                    for match, partner, theirs in rows
                ],
                total=total,
                filters=filters,
            )

    @staticmethod
    def _to_match(
        partner: User, partners_like: Reaction, matched_at: datetime
    ) -> MatchReadSchema:
        return MatchReadSchema(
            user=UserPublicSchema.model_validate(partner),
            contact=MatchContactSchema.model_validate(partner.telegram),
            message=partners_like.message,
            is_super=partners_like.is_super,
            matched_at=matched_at,
        )
