from datetime import datetime
from typing import Annotated, Literal

from ...core.schemas.base import BaseFilterSchema, BaseSchema, BaseUpdateSchema
from ...core.schemas.validators import NonNullable
from ..enums import ReportReason, ReportStatus
from .types import Comment


class ReportReadSchema(BaseSchema):
    id: int
    reporter_id: int
    target_id: int
    reason: ReportReason
    comment: str | None
    status: ReportStatus
    created_at: datetime
    updated_at: datetime


class ReportCreateSchema(BaseSchema):
    """The reporter comes from the request context, not from the payload."""

    target_id: int
    reason: ReportReason
    comment: Comment | None = None


# Reviewing closes a report; it is never set back to open.
type ReviewStatus = Literal[ReportStatus.RESOLVED, ReportStatus.DISMISSED]


class ReportUpdateSchema(BaseUpdateSchema):
    status: Annotated[ReviewStatus | None, NonNullable] = None


class ReportFilterSchema(BaseFilterSchema):
    order_by: Literal["created_at"] = "created_at"
    reporter_id: int | None = None
    target_id: int | None = None
    reason: ReportReason | None = None
    status: ReportStatus | None = None
