from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint, or_
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database.alchemy.mixins import CreatedAtMixin
from ...core.database.alchemy.models import Base
from ...core.database.alchemy.types import enum_type
from ..constants import MAX_MESSAGE_LENGTH
from ..enums import ReactionAction


class Reaction(CreatedAtMixin, Base):
    __tablename__ = "reactions"

    from_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    to_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    action: Mapped[ReactionAction] = mapped_column(
        enum_type(ReactionAction, name="reaction_action_enum")
    )
    is_super: Mapped[bool] = mapped_column(default=False, server_default="false")
    message: Mapped[str | None] = mapped_column(String(MAX_MESSAGE_LENGTH))

    __table_args__ = (
        UniqueConstraint(from_user_id, to_user_id, name="uq_reaction_pair"),
        CheckConstraint(from_user_id != to_user_id, name="not_self"),
        CheckConstraint(
            or_(is_super.is_(False), action == ReactionAction.LIKE),
            name="super_only_on_like",
        ),
        CheckConstraint(
            or_(message.is_(None), action == ReactionAction.LIKE),
            name="message_only_on_like",
        ),
    )
