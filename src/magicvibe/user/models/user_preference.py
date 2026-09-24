from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, and_
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database.alchemy.mixins import TimestampMixin
from ...core.database.alchemy.models import Base
from ...core.database.alchemy.types import enum_type
from ..constants import MAX_PROFILE_AGE, MIN_PROFILE_AGE
from ..enums import UserProfileGender


class UserPreference(TimestampMixin, Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    min_age: Mapped[int] = mapped_column(
        SmallInteger, default=MIN_PROFILE_AGE, server_default=str(MIN_PROFILE_AGE)
    )
    max_age: Mapped[int] = mapped_column(
        SmallInteger, default=MAX_PROFILE_AGE, server_default=str(MAX_PROFILE_AGE)
    )
    gender: Mapped[UserProfileGender | None] = mapped_column(
        enum_type(UserProfileGender, name="user_profile_gender_enum"), default=None
    )

    __table_args__ = (
        CheckConstraint(min_age <= max_age, name="age_range"),
        CheckConstraint(
            and_(min_age >= MIN_PROFILE_AGE, max_age <= MAX_PROFILE_AGE),
            name="age_bounds",
        ),
    )
