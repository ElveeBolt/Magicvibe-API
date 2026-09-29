from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database.alchemy.mixins import TimestampMixin
from ...core.database.alchemy.models import Base
from ...core.database.alchemy.types import enum_type
from ..constants import MAX_COMMENT_LENGTH
from ..enums import PlanCode


class Subscription(TimestampMixin, Base):
    """A period of premium. Current while `starts_at <= now() < expires_at`;
    free users have no row."""

    __tablename__ = "subscriptions"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    plan: Mapped[PlanCode] = mapped_column(enum_type(PlanCode, name="plan_code_enum"))
    # Set only by the database default, never taken from the API.
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # `starts_at` + the plan's duration; set to now to end the period early.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    comment: Mapped[str | None] = mapped_column(String(MAX_COMMENT_LENGTH))

    __table_args__ = (
        CheckConstraint(expires_at > starts_at, name="expires_after_start"),
        CheckConstraint(plan != PlanCode.FREE, name="paid_plan_only"),
        # Current subscription lookup.
        Index(None, user_id, expires_at),
    )
