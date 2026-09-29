from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from magicvibe.exceptions import constraint_name
from magicvibe.subscription.enums import PlanCode
from magicvibe.subscription.models import Subscription
from tests.factories import create_subscription, create_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def test_expires_after_start(session: AsyncSession) -> None:
    user = await create_user(session)

    with pytest.raises(IntegrityError) as error:
        await create_subscription(
            session, user, started=timedelta(0), expires_in=timedelta(0)
        )

    assert constraint_name(error.value) == "ck_subscriptions_expires_after_start"


async def test_paid_plan_only(session: AsyncSession) -> None:
    user = await create_user(session)
    session.add(
        Subscription(
            user_id=user.id,
            plan=PlanCode.FREE,
            expires_at=func.now() + timedelta(days=7),
        )
    )

    with pytest.raises(IntegrityError) as error:
        await session.flush()

    assert constraint_name(error.value) == "ck_subscriptions_paid_plan_only"
