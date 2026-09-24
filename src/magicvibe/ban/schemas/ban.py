from datetime import UTC, datetime
from typing import Annotated, Literal, Self

from pydantic import model_validator

from ...core.schemas.base import BaseFilterSchema, BaseSchema, BaseUpdateSchema
from ...core.schemas.validators import NonNullable
from ..enums import BanReason
from .types import Comment


class BanReadSchema(BaseSchema):
    id: int
    user_id: int
    reason: BanReason
    comment: str | None
    expires_at: datetime | None
    lifted_at: datetime | None
    lift_comment: str | None
    created_at: datetime
    updated_at: datetime


class BanCreateSchema(BaseSchema):
    user_id: int
    reason: BanReason
    comment: Comment | None = None
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_expires_in_future(self) -> Self:
        if self.expires_at is not None and self.expires_at <= datetime.now(UTC):
            raise ValueError("Ban expiry must be in the future")
        return self


class BanUpdateSchema(BaseUpdateSchema):
    reason: Annotated[BanReason | None, NonNullable] = None
    comment: Comment | None = None
    expires_at: datetime | None = None


class BanLiftSchema(BaseSchema):
    lift_comment: Comment | None = None


class BanFilterSchema(BaseFilterSchema):
    order_by: Literal["created_at"] = "created_at"
    user_id: int | None = None
    reason: BanReason | None = None
