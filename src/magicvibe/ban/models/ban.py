from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database.alchemy.mixins import TimestampMixin
from ...core.database.alchemy.models import Base
from ...core.database.alchemy.types import enum_type
from ..constants import MAX_COMMENT_LENGTH
from ..enums import BanReason


class Ban(TimestampMixin, Base):
    __tablename__ = "bans"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reason: Mapped[BanReason] = mapped_column(
        enum_type(BanReason, name="ban_reason_enum")
    )
    comment: Mapped[str | None] = mapped_column(String(MAX_COMMENT_LENGTH))
    lifted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lift_comment: Mapped[str | None] = mapped_column(String(MAX_COMMENT_LENGTH))

    __table_args__ = (
        Index(None, user_id, unique=True, postgresql_where=lifted_at.is_(None)),
        Index(None, user_id, "created_at"),
    )
