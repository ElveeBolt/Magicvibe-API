from datetime import datetime
from typing import Literal

from ...core.schemas.base import BaseFilterSchema, BaseSchema
from ..enums import PlanCode
from .types import Comment


class SubscriptionReadSchema(BaseSchema):
    id: int
    user_id: int
    plan: PlanCode
    starts_at: datetime
    expires_at: datetime
    comment: str | None
    created_at: datetime
    updated_at: datetime


class SubscriptionCreateSchema(BaseSchema):
    """Premium for `user_id`, starting now. The start and the end come from
    the database and the plan, never from the request."""

    user_id: int
    # The free plan has no subscriptions.
    plan: Literal[PlanCode.PREMIUM] = PlanCode.PREMIUM
    comment: Comment | None = None


class SubscriptionFilterSchema(BaseFilterSchema):
    order_by: Literal["created_at"] = "created_at"
    user_id: int | None = None


class PlanReadSchema(BaseSchema):
    """The plan that applies to a user now."""

    code: PlanCode
    name: str
    daily_like_limit: int
    daily_superlike_limit: int
    can_see_likers: bool
    # End of the current subscription; null on the free plan.
    expires_at: datetime | None
