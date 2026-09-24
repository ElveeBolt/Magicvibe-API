from datetime import datetime
from typing import Annotated

from ...core.schemas.base import BaseFilterSchema, BaseSchema, BaseUpdateSchema
from ...core.schemas.validators import NonNullable
from .types import FirstName, LanguageCode, LastName, Username


class UserTelegramReadSchema(BaseSchema):
    telegram_id: int
    first_name: str
    last_name: str | None
    username: str | None
    language_code: str | None
    is_premium: bool
    created_at: datetime
    updated_at: datetime


class UserTelegramCreateSchema(BaseSchema):
    telegram_id: int
    first_name: FirstName
    last_name: LastName | None = None
    username: Username | None = None
    language_code: LanguageCode | None = None
    is_premium: bool = False


class UserTelegramUpdateSchema(BaseUpdateSchema):
    first_name: Annotated[FirstName | None, NonNullable] = None
    last_name: LastName | None = None
    username: Username | None = None
    language_code: LanguageCode | None = None
    is_premium: Annotated[bool | None, NonNullable] = None


class UserTelegramFilterSchema(BaseFilterSchema):
    telegram_id: int | None = None
    username: str | None = None
    language_code: str | None = None
    is_premium: bool | None = None
