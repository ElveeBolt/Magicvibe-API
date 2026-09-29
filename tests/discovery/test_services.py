from datetime import UTC, datetime

import pytest

from magicvibe.core.exceptions import ConflictError, ErrorCode
from magicvibe.dependencies import get_uow
from magicvibe.discovery.services import DiscoveryService
from magicvibe.user.schemas.user import UserReadSchema


async def test_browsing_without_a_profile_is_rejected() -> None:
    now = datetime.now(UTC)
    viewer = UserReadSchema.model_validate(
        {
            "id": 1,
            "status": "active",
            "last_seen_at": now,
            "created_at": now,
            "updated_at": now,
            "profile": None,
            "telegram": None,
            "preference": None,
        }
    )

    # The check comes before the unit of work opens, so no database is needed.
    with pytest.raises(ConflictError) as error:
        await DiscoveryService(get_uow()).get_next_candidate(viewer=viewer)

    assert error.value.code is ErrorCode.PROFILE_REQUIRED
    assert error.value.status_code == 409
