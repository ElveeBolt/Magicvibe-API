from datetime import date, datetime
from typing import Annotated

from pydantic import computed_field

from ...core.schemas.base import BaseFilterSchema, BaseSchema, BaseUpdateSchema
from ...core.schemas.validators import NonNullable
from ..enums import UserProfileGender
from ..utils import calculate_age
from .types import Bio, BirthDate, Name


class UserProfileReadSchema(BaseSchema):
    name: str
    birth_date: date
    gender: UserProfileGender
    bio: str
    is_visible: bool
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def age(self) -> int:
        return calculate_age(self.birth_date)


class UserProfileCreateSchema(BaseSchema):
    name: Name
    birth_date: BirthDate
    gender: UserProfileGender
    bio: Bio
    is_visible: bool = True


class UserProfileUpdateSchema(BaseUpdateSchema):
    name: Annotated[Name | None, NonNullable] = None
    birth_date: Annotated[BirthDate | None, NonNullable] = None
    gender: Annotated[UserProfileGender | None, NonNullable] = None
    bio: Annotated[Bio | None, NonNullable] = None
    is_visible: Annotated[bool | None, NonNullable] = None


class UserProfileFilterSchema(BaseFilterSchema):
    name: str | None = None
    birth_date: date | None = None
    gender: UserProfileGender | None = None
    is_visible: bool | None = None
