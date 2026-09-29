from typing import Literal

from ...core.schemas.base import BaseFilterSchema, BaseSchema, SortOrder


class RegionCityReadSchema(BaseSchema):
    id: int
    region_id: int
    katotth_code: str
    name: str
    name_en: str


class RegionCityFilterSchema(BaseFilterSchema):
    order_by: Literal["name"] = "name"
    order: SortOrder = SortOrder.ASC
