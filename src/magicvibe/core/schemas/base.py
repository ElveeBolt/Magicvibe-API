from enum import StrEnum
from typing import Any, ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class BaseUpdateSchema(BaseModel):
    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update")
        return self


class BaseFilterSchema(BaseModel):
    order_by: str | None = Field(default=None)
    order: SortOrder | None = Field(default=SortOrder.DESC)
    page_size: int = Field(default=10, ge=1)
    page: int = Field(default=1, ge=1)

    _PAGINATION_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"order_by", "order", "page_size", "page"}
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def descending(self) -> bool:
        return self.order == SortOrder.DESC

    def to_filter_dict(self) -> dict[str, Any]:
        return {
            k: v
            for k, v in self.model_dump(exclude_none=True).items()
            if k not in self._PAGINATION_FIELDS
        }


class BaseCountSchema(BaseModel):
    count: int


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    pages: int
    page_size: int

    @classmethod
    def build(
        cls, items: list[T], total: int, filters: BaseFilterSchema
    ) -> PaginatedResponse[T]:
        pages = (total + filters.page_size - 1) // filters.page_size if total else 1
        return cls(
            items=items,
            total=total,
            page=filters.page,
            pages=pages,
            page_size=filters.page_size,
        )
