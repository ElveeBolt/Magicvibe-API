from datetime import date
from typing import TYPE_CHECKING

import pytest
from sqlalchemy.exc import IntegrityError

from magicvibe.exceptions import constraint_name
from magicvibe.user.enums import DatingGoal, UserProfileGender
from magicvibe.user.models import UserProfile
from tests.factories import create_preference, create_profile, create_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def test_bio_is_never_empty(session: AsyncSession) -> None:
    user = await create_user(session)

    with pytest.raises(IntegrityError) as error:
        await create_profile(session, user, bio="")

    assert constraint_name(error.value) == "ck_user_profiles_bio_not_empty"


async def test_bio_may_be_null(session: AsyncSession) -> None:
    profile = await create_profile(session, await create_user(session), bio=None)

    assert profile.bio is None


async def test_preference_age_range(session: AsyncSession) -> None:
    user = await create_user(session)

    with pytest.raises(IntegrityError) as error:
        await create_preference(session, user, min_age=30, max_age=20)

    assert constraint_name(error.value) == "ck_user_preferences_age_range"


async def test_preference_age_bounds(session: AsyncSession) -> None:
    user = await create_user(session)

    with pytest.raises(IntegrityError) as error:
        await create_preference(session, user, min_age=17, max_age=50)

    assert constraint_name(error.value) == "ck_user_preferences_age_bounds"


async def test_profile_city_must_exist(session: AsyncSession) -> None:
    user = await create_user(session)
    session.add(
        UserProfile(
            user_id=user.id,
            name="Ann",
            birth_date=date(2000, 1, 1),
            gender=UserProfileGender.FEMALE,
            city_id=999_999,
            dating_goal=DatingGoal.CASUAL,
        )
    )

    with pytest.raises(IntegrityError) as error:
        await session.flush()

    assert constraint_name(error.value) == "fk_user_profiles_city_id_cities"
