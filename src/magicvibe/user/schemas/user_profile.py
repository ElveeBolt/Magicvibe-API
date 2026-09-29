from datetime import date, datetime
from typing import Annotated

from pydantic import computed_field

from ...core.schemas.base import BaseFilterSchema, BaseSchema, BaseUpdateSchema
from ...core.schemas.validators import NonNullable
from ...region.schemas.region_city import RegionCityReadSchema
from ..enums import DatingGoal, UserProfileGender
from ..utils import calculate_age
from .types import Bio, BirthDate, Name


class UserProfileReadSchema(BaseSchema):
    name: str
    birth_date: date
    gender: UserProfileGender
    bio: str | None
    city_id: int
    city: RegionCityReadSchema
    dating_goal: DatingGoal
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
    city_id: int
    dating_goal: DatingGoal
    bio: Bio | None = None
    is_visible: bool = True


class UserProfileUpdateSchema(BaseUpdateSchema):
    name: Annotated[Name | None, NonNullable] = None
    birth_date: Annotated[BirthDate | None, NonNullable] = None
    gender: Annotated[UserProfileGender | None, NonNullable] = None
    city_id: Annotated[int | None, NonNullable] = None
    dating_goal: Annotated[DatingGoal | None, NonNullable] = None
    # Optional: `null` removes the bio.
    bio: Bio | None = None
    is_visible: Annotated[bool | None, NonNullable] = None


class UserProfileFilterSchema(BaseFilterSchema):
    name: str | None = None
    birth_date: date | None = None
    gender: UserProfileGender | None = None
    dating_goal: DatingGoal | None = None
    is_visible: bool | None = None
