from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import StringConstraints, model_validator

from ...core.schemas.base import BaseFilterSchema, BaseSchema
from ...user.schemas.user import UserPublicSchema
from ..constants import MAX_MESSAGE_LENGTH
from ..enums import ReactionAction

type Message = Annotated[
    str,
    StringConstraints(
        min_length=1, max_length=MAX_MESSAGE_LENGTH, strip_whitespace=True
    ),
]


class ReactionReadSchema(BaseSchema):
    id: int
    from_user_id: int
    to_user_id: int
    action: ReactionAction
    is_super: bool
    message: str | None
    created_at: datetime


class ReactionCreateSchema(BaseSchema):
    """Reaction payload; the swiping user comes from the request context."""

    to_user_id: int
    action: ReactionAction
    is_super: bool = False
    message: Message | None = None

    @model_validator(mode="after")
    def validate_like_only_fields(self) -> Self:
        if self.action is ReactionAction.LIKE:
            return self
        if self.is_super:
            raise ValueError("Only a like can be super")
        if self.message is not None:
            raise ValueError("Only a like can have a message")
        return self


class MatchContactSchema(BaseSchema):
    """The partner's Telegram contact; shown only in match data."""

    telegram_id: int
    first_name: str
    last_name: str | None
    username: str | None


class MatchReadSchema(BaseSchema):
    """A match as seen by one of its two users. The only place with the
    partner's Telegram contact and their like message."""

    user: UserPublicSchema
    contact: MatchContactSchema
    message: str | None
    is_super: bool
    matched_at: datetime


class ReactionResultReadSchema(BaseSchema):
    reaction: ReactionReadSchema
    match: MatchReadSchema | None


class ReactionFilterSchema(BaseFilterSchema):
    from_user_id: int | None = None
    to_user_id: int | None = None
    action: ReactionAction | None = None


class MatchFilterSchema(BaseFilterSchema):
    order_by: Literal["matched_at"] = "matched_at"
