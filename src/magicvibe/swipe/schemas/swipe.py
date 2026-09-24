from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import StringConstraints, model_validator

from ...core.schemas.base import BaseFilterSchema, BaseSchema
from ...user.schemas.user import UserPublicSchema
from ..constants import MAX_MESSAGE_LENGTH
from ..enums import SwipeAction

type Message = Annotated[
    str,
    StringConstraints(
        min_length=1, max_length=MAX_MESSAGE_LENGTH, strip_whitespace=True
    ),
]


class SwipeReadSchema(BaseSchema):
    id: int
    from_user_id: int
    to_user_id: int
    action: SwipeAction
    is_super: bool
    message: str | None
    created_at: datetime


class SwipeCreateSchema(BaseSchema):
    """Swipe payload; the swiping user comes from the request context."""

    to_user_id: int
    action: SwipeAction
    is_super: bool = False
    message: Message | None = None

    @model_validator(mode="after")
    def validate_like_only_fields(self) -> Self:
        if self.action is SwipeAction.LIKE:
            return self
        if self.is_super:
            raise ValueError("Only a like can be super")
        if self.message is not None:
            raise ValueError("Only a like can have a message")
        return self


class MatchedUserSchema(UserPublicSchema):
    """Public profile plus the handle needed to start a conversation."""

    username: str | None


class MatchReadSchema(BaseSchema):
    """A mutual like as seen by one of its two members."""

    user: MatchedUserSchema
    matched_at: datetime


class SwipeResultReadSchema(BaseSchema):
    swipe: SwipeReadSchema
    match: MatchReadSchema | None


class SwipeFilterSchema(BaseFilterSchema):
    from_user_id: int | None = None
    to_user_id: int | None = None
    action: SwipeAction | None = None


class MatchFilterSchema(BaseFilterSchema):
    order_by: Literal["matched_at"] = "matched_at"
