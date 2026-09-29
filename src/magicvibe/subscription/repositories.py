from datetime import timedelta

from sqlalchemy import exists, func, select

from ..core.database.alchemy.repository import AlchemyRepository
from .constants import Plan
from .models import Subscription


class SubscriptionRepository(AlchemyRepository[Subscription, int]):
    model = Subscription

    async def get_current(self, user_id: int) -> Subscription | None:
        """The subscription with `starts_at <= now() < expires_at`; there is at
        most one."""
        stmt = self._get_base_stmt().where(
            Subscription.user_id == user_id,
            Subscription.starts_at <= func.now(),
            Subscription.expires_at > func.now(),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_unexpired(self, user_id: int) -> bool:
        """Whether the user has a subscription that has not ended yet.

        Used for the one-current-subscription rule instead of `get_current`:
        `now()` is the start of the transaction, so a grant that waited for the
        user lock would not see a subscription committed meanwhile (its
        `starts_at` is later than this transaction's `now()`). No subscription
        starts in the future otherwise, so "not ended" is the right test here.
        """
        stmt = select(
            exists().where(
                Subscription.user_id == user_id,
                Subscription.expires_at > func.now(),
            )
        )
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def create_for(
        self, user_id: int, plan: Plan, comment: str | None
    ) -> Subscription:
        """Starts now, by the database clock, and lasts the plan's duration."""
        if plan.duration_days is None:
            raise ValueError(f"Plan {plan.code} has no end date to subscribe to")

        return await self.create(
            {
                "user_id": user_id,
                "plan": plan.code,
                "comment": comment,
                "expires_at": func.now() + timedelta(days=plan.duration_days),
            }
        )

    async def end(self, id_: int) -> Subscription | None:
        """Ends the period now, by the database clock."""
        return await self.update(id_=id_, data={"expires_at": func.now()})
