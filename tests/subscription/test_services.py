from datetime import timedelta
from typing import TYPE_CHECKING

from sqlalchemy import func, update

from magicvibe.subscription.enums import PlanCode
from magicvibe.subscription.models import Subscription
from magicvibe.subscription.services import SubscriptionService
from tests.factories import create_subscription, create_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from magicvibe.uow import UnitOfWork


async def plan_code(uow: UnitOfWork, user_id: int) -> PlanCode:
    async with uow:
        plan, _ = await SubscriptionService(uow).get_effective_plan(user_id)
    return plan.code


async def test_effective_plan_around_expires_at(
    uow: UnitOfWork, session: AsyncSession
) -> None:
    user = await create_user(session)
    subscription = await create_subscription(session, user)

    async def expires_in(delta: timedelta) -> PlanCode:
        await session.execute(
            update(Subscription)
            .where(Subscription.id == subscription.id)
            .values(expires_at=func.now() + delta)
        )
        await session.commit()
        return await plan_code(uow, user.id)

    assert await expires_in(timedelta(microseconds=1)) is PlanCode.PREMIUM
    assert await expires_in(timedelta(0)) is PlanCode.FREE
    assert await expires_in(-timedelta(microseconds=1)) is PlanCode.FREE


async def test_future_subscription_is_not_current(
    uow: UnitOfWork, session: AsyncSession
) -> None:
    user = await create_user(session)
    await create_subscription(
        session, user, started=-timedelta(days=1), expires_in=timedelta(days=6)
    )

    assert await plan_code(uow, user.id) is PlanCode.FREE
