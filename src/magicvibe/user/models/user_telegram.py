from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database.alchemy.mixins import TimestampMixin
from ...core.database.alchemy.models import Base


class UserTelegram(TimestampMixin, Base):
    __tablename__ = "user_telegrams"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[str | None] = mapped_column(String(64))
    username: Mapped[str | None] = mapped_column(String(32))
    language_code: Mapped[str | None] = mapped_column(String(8))
    is_premium: Mapped[bool] = mapped_column(default=False, server_default="false")
