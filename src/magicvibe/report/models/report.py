from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database.alchemy.mixins import TimestampMixin
from ...core.database.alchemy.models import Base
from ...core.database.alchemy.types import enum_type
from ..constants import MAX_COMMENT_LENGTH
from ..enums import ReportReason, ReportStatus


class Report(TimestampMixin, Base):
    __tablename__ = "reports"

    reporter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    target_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    reason: Mapped[ReportReason] = mapped_column(
        enum_type(ReportReason, name="report_reason_enum")
    )
    comment: Mapped[str | None] = mapped_column(String(MAX_COMMENT_LENGTH))
    status: Mapped[ReportStatus] = mapped_column(
        enum_type(ReportStatus, name="report_status_enum"),
        default=ReportStatus.OPEN,
        server_default=ReportStatus.OPEN.value,
    )

    __table_args__ = (
        CheckConstraint(reporter_id != target_id, name="not_self"),
        Index(None, status, "created_at"),
    )
