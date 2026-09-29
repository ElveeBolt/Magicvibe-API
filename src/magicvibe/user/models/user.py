from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database.alchemy.mixins import TimestampMixin
from ...core.database.alchemy.models import Base
from ...core.database.alchemy.types import enum_type
from ..enums import UserStatus
from .user_preference import UserPreference
from .user_profile import UserProfile
from .user_telegram import UserTelegram


class User(TimestampMixin, Base):
    __tablename__ = "users"

    status: Mapped[UserStatus] = mapped_column(
        enum_type(UserStatus, name="user_status_enum"),
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    profile: Mapped[UserProfile | None] = relationship(
        cascade="all, delete-orphan", lazy="joined"
    )
    telegram: Mapped[UserTelegram | None] = relationship(
        cascade="all, delete-orphan", lazy="joined"
    )
    preference: Mapped[UserPreference | None] = relationship(
        cascade="all, delete-orphan", lazy="joined"
    )
