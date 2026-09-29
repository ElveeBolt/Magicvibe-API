from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError

from magicvibe.user.constants import (
    MAX_BIO_LENGTH,
    MAX_PROFILE_AGE,
    MAX_PROFILE_NAME_LENGTH,
    MIN_PROFILE_AGE,
)
from magicvibe.user.schemas.user_profile import (
    UserProfileCreateSchema,
    UserProfileUpdateSchema,
)


def years_ago(years: int) -> date:
    # The same "today" the age check uses.
    today = datetime.now(UTC).date()
    try:
        return today.replace(year=today.year - years)
    except ValueError:  # 29 February
        return today.replace(year=today.year - years, day=28)


def profile(**fields: object) -> dict[str, object]:
    return {
        "name": "Ann",
        "birth_date": years_ago(30),
        "gender": "female",
        "city_id": 1,
        "dating_goal": "chatting",
        **fields,
    }


def rejected_fields(data: dict[str, object]) -> list[tuple[object, ...]]:
    with pytest.raises(ValidationError) as error:
        UserProfileCreateSchema.model_validate(data)
    return [item["loc"] for item in error.value.errors()]


@pytest.mark.parametrize(
    "birth_date",
    [years_ago(MIN_PROFILE_AGE), years_ago(MAX_PROFILE_AGE + 1) + timedelta(days=1)],
    ids=["18th-birthday-today", "last-day-of-age-100"],
)
def test_age_boundaries_are_accepted(birth_date: date) -> None:
    UserProfileCreateSchema.model_validate(profile(birth_date=birth_date))


@pytest.mark.parametrize(
    "birth_date",
    [years_ago(MIN_PROFILE_AGE) + timedelta(days=1), years_ago(MAX_PROFILE_AGE + 1)],
    ids=["day-before-18th-birthday", "101st-birthday"],
)
def test_ages_outside_the_range_are_rejected(birth_date: date) -> None:
    assert rejected_fields(profile(birth_date=birth_date)) == [("birth_date",)]


def test_bio_is_optional_and_stripped() -> None:
    assert UserProfileCreateSchema.model_validate(profile()).bio is None
    assert UserProfileCreateSchema.model_validate(profile(bio=" Hi ")).bio == "Hi"


@pytest.mark.parametrize(
    ("bio", "accepted"),
    [("", False), ("   ", False), ("x" * MAX_BIO_LENGTH, True), ("x" * 501, False)],
)
def test_bio_length(bio: str, accepted: bool) -> None:
    if accepted:
        UserProfileCreateSchema.model_validate(profile(bio=bio))
    else:
        assert rejected_fields(profile(bio=bio)) == [("bio",)]


@pytest.mark.parametrize(
    ("name", "accepted"),
    [("", False), ("x" * MAX_PROFILE_NAME_LENGTH, True), ("x" * 65, False)],
)
def test_name_length(name: str, accepted: bool) -> None:
    if accepted:
        UserProfileCreateSchema.model_validate(profile(name=name))
    else:
        assert rejected_fields(profile(name=name)) == [("name",)]


def test_dating_goal_values() -> None:
    for goal in ("relationship", "friendship", "casual", "chatting"):
        UserProfileCreateSchema.model_validate(profile(dating_goal=goal))
    assert rejected_fields(profile(dating_goal="marriage")) == [("dating_goal",)]


def test_update_can_clear_bio_but_not_required_fields() -> None:
    assert UserProfileUpdateSchema.model_validate({"bio": None}).bio is None
    for field in ("name", "city_id", "dating_goal"):
        with pytest.raises(ValidationError):
            UserProfileUpdateSchema.model_validate({field: None})
