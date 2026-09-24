from datetime import datetime
from typing import Annotated, Self

from pydantic import model_validator

from ...core.schemas.base import BaseSchema, BaseUpdateSchema
from ...core.schemas.validators import NonNullable
from ..constants import MAX_PROFILE_AGE, MIN_PROFILE_AGE
from ..enums import UserProfileGender
from .types import Age
from .validators import validate_age_bounds


class UserPreferenceReadSchema(BaseSchema):
    min_age: int
    max_age: int
    gender: UserProfileGender | None
    created_at: datetime
    updated_at: datetime


class UserPreferenceCreateSchema(BaseSchema):
    min_age: Age = MIN_PROFILE_AGE
    max_age: Age = MAX_PROFILE_AGE
    gender: UserProfileGender | None = None

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        validate_age_bounds(min_age=self.min_age, max_age=self.max_age)
        return self


class UserPreferenceUpdateSchema(BaseUpdateSchema):
    min_age: Annotated[Age | None, NonNullable] = None
    max_age: Annotated[Age | None, NonNullable] = None
    gender: UserProfileGender | None = None
