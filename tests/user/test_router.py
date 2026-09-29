from typing import TYPE_CHECKING

from magicvibe.ban.enums import BanReason
from magicvibe.user.enums import UserStatus
from tests.conftest import acting_user
from tests.factories import create_ban, create_user

if TYPE_CHECKING:
    import httpx
    from sqlalchemy.ext.asyncio import AsyncSession

# Any endpoint that needs the acting user works here; discovery needs no body.
ACTING_USER_ENDPOINT = "/discovery/next"


async def test_unknown_acting_user(client: httpx.AsyncClient) -> None:
    response = await client.get(ACTING_USER_ENDPOINT, headers=acting_user(999_999))

    assert response.status_code == 404
    assert response.json()["code"] == "USER_NOT_FOUND"


async def test_deleted_acting_user(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session, status=UserStatus.DELETED)
    assert user.telegram is not None

    response = await client.get(
        ACTING_USER_ENDPOINT, headers=acting_user(user.telegram.telegram_id)
    )

    assert response.status_code == 404
    assert response.json()["code"] == "USER_NOT_FOUND"


async def test_banned_acting_user(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_ban(session, user, reason=BanReason.SCAM, comment="Fake shop")
    assert user.telegram is not None

    response = await client.get(
        ACTING_USER_ENDPOINT, headers=acting_user(user.telegram.telegram_id)
    )

    assert response.status_code == 403
    body = response.json()
    assert body["code"] == "USER_BANNED"
    assert body["ban"] == {"reason": "scam", "comment": "Fake shop"}
