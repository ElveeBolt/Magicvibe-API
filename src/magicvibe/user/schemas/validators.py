from typing import TYPE_CHECKING

from ..constants import MAX_PROFILE_AGE, MIN_PROFILE_AGE
from ..utils import calculate_age

if TYPE_CHECKING:
    from datetime import date

AGE_RANGE_ERROR = "min_age must not be greater than max_age"


def validate_age_range(birth_date: date) -> date:
    age = calculate_age(birth_date)

    if not MIN_PROFILE_AGE <= age <= MAX_PROFILE_AGE:
        raise ValueError(f"Age must be between {MIN_PROFILE_AGE} and {MAX_PROFILE_AGE}")

    return birth_date


def validate_age_bounds(min_age: int, max_age: int) -> None:
    """Shared by the request schemas and by the service, which re-checks the
    merged values a partial update produces."""
    if min_age > max_age:
        raise ValueError(AGE_RANGE_ERROR)
