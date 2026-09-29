from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database.alchemy.mixins import CreatedAtMixin
from ...core.database.alchemy.models import Base


class Match(CreatedAtMixin, Base):
    """Two users who liked each other. The pair is stored in a fixed order,
    which makes it unique in both directions and rules out a match with
    oneself. Created by the like that completes the pair."""

    __tablename__ = "matches"

    user_a_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user_b_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    __table_args__ = (
        UniqueConstraint(user_a_id, user_b_id, name="uq_match_pair"),
        CheckConstraint(user_a_id < user_b_id, name="ordered_pair"),
        Index(None, user_b_id),
    )
