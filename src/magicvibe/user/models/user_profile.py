from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, or_
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database.alchemy.mixins import TimestampMixin
from ...core.database.alchemy.models import Base
from ...core.database.alchemy.types import enum_type
from ...region.models import RegionCity
from ..constants import MAX_BIO_LENGTH, MAX_PROFILE_NAME_LENGTH
from ..enums import DatingGoal, UserProfileGender


class UserProfile(TimestampMixin, Base):
    """A row exists only when every required field is filled, so a user with a
    profile has a complete profile. A missing bio is null, never empty."""

    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    name: Mapped[str] = mapped_column(String(MAX_PROFILE_NAME_LENGTH))
    birth_date: Mapped[date] = mapped_column(Date)
    gender: Mapped[UserProfileGender] = mapped_column(
        enum_type(UserProfileGender, name="user_profile_gender_enum")
    )
    bio: Mapped[str | None] = mapped_column(String(MAX_BIO_LENGTH))
    # Cities are never deleted, so no `ON DELETE` action.
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    dating_goal: Mapped[DatingGoal] = mapped_column(
        enum_type(DatingGoal, name="dating_goal_enum")
    )
    is_visible: Mapped[bool] = mapped_column(default=True, server_default="true")

    city: Mapped[RegionCity] = relationship(lazy="joined")

    __table_args__ = (
        CheckConstraint(or_(bio.is_(None), bio != ""), name="bio_not_empty"),
    )
