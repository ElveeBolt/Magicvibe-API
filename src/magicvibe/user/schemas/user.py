from datetime import datetime
from typing import Annotated

from ...core.schemas.base import BaseFilterSchema, BaseSchema, BaseUpdateSchema
from ...core.schemas.validators import NonNullable
from ..enums import UserStatus
from .user_preference import UserPreferenceReadSchema
from .user_profile import UserProfileReadSchema
from .user_telegram import UserTelegramCreateSchema, UserTelegramReadSchema


class UserReadSchema(BaseSchema):
    id: int
    status: UserStatus
    deleted_at: datetime | None
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


class UserUpdateSchema(BaseUpdateSchema):
    status: Annotated[UserStatus | None, NonNullable] = None
    deleted_at: Annotated[datetime | None, NonNullable] = None


class UserFilterSchema(BaseFilterSchema):
    status: UserStatus | None = None
