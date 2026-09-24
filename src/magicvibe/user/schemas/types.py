from datetime import date
from typing import Annotated

from pydantic import AfterValidator, Field, StringConstraints

from ..constants import (
    MAX_BIO_LENGTH,
    MAX_PROFILE_AGE,
    MAX_PROFILE_NAME_LENGTH,
    MIN_PROFILE_AGE,
)
from .validators import validate_age_range

type FirstName = Annotated[
    str, StringConstraints(min_length=1, max_length=64, strip_whitespace=True)
]
type LastName = Annotated[str, StringConstraints(max_length=64, strip_whitespace=True)]
type Username = Annotated[str, StringConstraints(min_length=4, max_length=32)]
type LanguageCode = Annotated[str, StringConstraints(min_length=2, max_length=8)]

type Name = Annotated[
    str,
    StringConstraints(
        min_length=1, max_length=MAX_PROFILE_NAME_LENGTH, strip_whitespace=True
    ),
]
type BirthDate = Annotated[date, AfterValidator(validate_age_range)]
type Bio = Annotated[
    str,
    StringConstraints(min_length=1, max_length=MAX_BIO_LENGTH, strip_whitespace=True),
]

type Age = Annotated[int, Field(ge=MIN_PROFILE_AGE, le=MAX_PROFILE_AGE)]
