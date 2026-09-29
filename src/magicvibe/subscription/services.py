from typing import TYPE_CHECKING

from ..core.database.alchemy.service import AlchemyService
from ..core.exceptions import ConflictError, ErrorCode, NotFoundError
from ..core.schemas.base import BaseUpdateSchema
from ..user.enums import UserStatus
from .constants import PLANS, Plan
from .enums import PlanCode
from .schemas.subscription import (
    PlanReadSchema,
    SubscriptionCreateSchema,
    SubscriptionFilterSchema,
    SubscriptionReadSchema,
)

if TYPE_CHECKING:
    from ..uow import UnitOfWork
    from .models import Subscription
    from .repositories import SubscriptionRepository


class SubscriptionService(
    AlchemyService[
        # A subscription is never updated through the API, only ended.
        SubscriptionCreateSchema,
        BaseUpdateSchema,
        SubscriptionReadSchema,
        SubscriptionFilterSchema,
        int,
    ]
):
    schema = SubscriptionReadSchema
    uow: UnitOfWork

    @property
    def repository(self) -> SubscriptionRepository:  # type: ignore[override]
        return self.uow.subscription

    async def create(self, data: SubscriptionCreateSchema) -> SubscriptionReadSchema:
        """Grants premium. The user row is locked first, so two grants for one
        user cannot both see "no current subscription"."""
        async with self.uow:
            user = await self.uow.user.get_for_update(data.user_id)

            if user is None:
                raise NotFoundError("User not found")

            if user.status is UserStatus.BANNED:
                raise ConflictError(
                    "Premium cannot be granted to a banned user",
                    code=ErrorCode.TARGET_USER_BANNED,
                )

            if await self.repository.has_unexpired(data.user_id):
                raise ConflictError(
                    "The user already has current premium",
                    code=ErrorCode.PREMIUM_ALREADY_ACTIVE,
                )

            subscription = await self.repository.create_for(
                data.user_id, PLANS[data.plan], data.comment
            )
            return self._to_schema(subscription)

    async def end(self, subscription_id: int) -> SubscriptionReadSchema:
        """Ends a current subscription now; the change applies at once."""
        async with self.uow:
            subscription = await self.repository.get(id_=subscription_id)

            if subscription is None:
                raise NotFoundError("Subscription not found")

            current = await self.repository.get_current(subscription.user_id)

            if current is None or current.id != subscription.id:
                raise ConflictError("The subscription is not current")

            ended = await self.repository.end(subscription.id)
            assert ended is not None  # read above in the same transaction
            return self._to_schema(ended)

    async def get_plan(self, user_id: int) -> PlanReadSchema:
        async with self.uow:
            if not await self.uow.user.exists(id_=user_id):
                raise NotFoundError("User not found")

            plan, current = await self.get_effective_plan(user_id)
            return PlanReadSchema(
                code=plan.code,
                name=plan.name,
                daily_like_limit=plan.daily_like_limit,
                daily_superlike_limit=plan.daily_superlike_limit,
                can_see_likers=plan.can_see_likers,
                expires_at=current.expires_at if current else None,
            )

    async def get_effective_plan(
        self, user_id: int
    ) -> tuple[Plan, Subscription | None]:
        """The plan that applies now: premium during a current subscription,
        otherwise free. Runs inside the caller's unit of work."""
        current = await self.repository.get_current(user_id)

        if current is None:
            return PLANS[PlanCode.FREE], None

        return PLANS[current.plan], current
