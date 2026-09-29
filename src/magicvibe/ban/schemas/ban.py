from datetime import datetime
from typing import Annotated, Literal

from ...core.schemas.base import BaseFilterSchema, BaseSchema, BaseUpdateSchema
from ...core.schemas.validators import NonNullable
from ..enums import BanReason
from .types import Comment


class BanReadSchema(BaseSchema):
    id: int
    user_id: int
    reason: BanReason
    comment: str | None
    lifted_at: datetime | None
    lift_comment: str | None
    created_at: datetime
    updated_at: datetime


class BanCreateSchema(BaseSchema):
    user_id: int
    reason: BanReason
    comment: Comment | None = None


class BanUpdateSchema(BaseUpdateSchema):
    reason: Annotated[BanReason | None, NonNullable] = None
    comment: Comment | None = None


class BanLiftSchema(BaseSchema):
    lift_comment: Comment | None = None


class BanFilterSchema(BaseFilterSchema):
    order_by: Literal["created_at"] = "created_at"
    user_id: int | None = None
    reason: BanReason | None = None
