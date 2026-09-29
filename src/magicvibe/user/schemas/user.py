from datetime import datetime

from ...core.schemas.base import BaseFilterSchema, BaseSchema
from ..enums import UserStatus
from .user_preference import UserPreferenceReadSchema
from .user_profile import UserProfileReadSchema
from .user_telegram import UserTelegramCreateSchema, UserTelegramReadSchema


class UserReadSchema(BaseSchema):
    id: int
    status: UserStatus
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime
    profile: UserProfileReadSchema | None
    telegram: UserTelegramReadSchema | None
    preference: UserPreferenceReadSchema | None


class UserPublicSchema(BaseSchema):
    """What one user is allowed to see about another (discovery, matches)."""

    id: int
    profile: UserProfileReadSchema | None


class UserCreateSchema(BaseSchema):
    telegram: UserTelegramCreateSchema


class UserFilterSchema(BaseFilterSchema):
    status: UserStatus | None = None
