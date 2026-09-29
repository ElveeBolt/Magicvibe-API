from datetime import datetime
from typing import Annotated, Self

from pydantic import model_validator

from ...core.schemas.base import BaseSchema, BaseUpdateSchema
from ...core.schemas.validators import NonNullable
from ...region.schemas.region_city import RegionCityReadSchema
from ..constants import MAX_PROFILE_AGE, MIN_PROFILE_AGE
from ..enums import DatingGoal, UserProfileGender
from .types import Age
from .validators import validate_age_bounds


class UserPreferenceReadSchema(BaseSchema):
    min_age: int
    max_age: int
    gender: UserProfileGender | None
    city_id: int | None
    city: RegionCityReadSchema | None
    dating_goal: DatingGoal | None
    created_at: datetime
    updated_at: datetime


class UserPreferenceCreateSchema(BaseSchema):
    min_age: Age = MIN_PROFILE_AGE
    max_age: Age = MAX_PROFILE_AGE
    # `null` (or omitted) means any.
    gender: UserProfileGender | None = None
    city_id: int | None = None
    dating_goal: DatingGoal | None = None

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        validate_age_bounds(min_age=self.min_age, max_age=self.max_age)
        return self


class UserPreferenceUpdateSchema(BaseUpdateSchema):
    min_age: Annotated[Age | None, NonNullable] = None
    max_age: Annotated[Age | None, NonNullable] = None
    # `null` means any.
    gender: UserProfileGender | None = None
    city_id: int | None = None
    dating_goal: DatingGoal | None = None
