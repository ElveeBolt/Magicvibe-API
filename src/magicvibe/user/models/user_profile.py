from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database.alchemy.mixins import TimestampMixin
from ...core.database.alchemy.models import Base
from ...core.database.alchemy.types import enum_type
from ..constants import MAX_PROFILE_NAME_LENGTH
from ..enums import UserProfileGender


class UserProfile(TimestampMixin, Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    name: Mapped[str] = mapped_column(String(MAX_PROFILE_NAME_LENGTH))
    birth_date: Mapped[date] = mapped_column(Date)
    gender: Mapped[UserProfileGender] = mapped_column(
        enum_type(UserProfileGender, name="user_profile_gender_enum")
    )
    bio: Mapped[str] = mapped_column(Text)
    is_visible: Mapped[bool] = mapped_column(default=True, server_default="true")

    __table_args__ = (
        Index(
            "ix_user_profiles_discovery",
            gender,
            birth_date,
            postgresql_where=is_visible.is_(True),
        ),
    )
