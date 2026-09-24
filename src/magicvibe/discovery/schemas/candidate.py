from ...core.schemas.base import BaseSchema
from ...user.schemas.user import UserPublicSchema


class NextCandidateSchema(BaseSchema):
    """`candidate` is null when the user has seen everyone available."""

    candidate: UserPublicSchema | None
