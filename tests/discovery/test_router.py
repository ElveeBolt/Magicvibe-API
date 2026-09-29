from typing import TYPE_CHECKING

from magicvibe.user.enums import UserProfileGender
from tests.conftest import acting_user
from tests.factories import create_city, create_profile, create_region, create_user

if TYPE_CHECKING:
    import httpx
    from sqlalchemy.ext.asyncio import AsyncSession


async def test_candidate_comes_with_its_city(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    viewer = await create_user(session)
    await create_profile(session, viewer, gender=UserProfileGender.MALE)
    candidate = await create_user(session)
    city = await create_city(session, await create_region(session), name="Черкаси")
    await create_profile(session, candidate, city=city)
    assert viewer.telegram is not None

    response = await client.get(
        "/discovery/next", headers=acting_user(viewer.telegram.telegram_id)
    )

    assert response.status_code == 200
    profile = response.json()["candidate"]["profile"]
    assert profile["city"]["name"] == "Черкаси"
    assert profile["dating_goal"] == "relationship"
