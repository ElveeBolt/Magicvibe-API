from typing import Literal

from ...core.schemas.base import BaseFilterSchema, BaseSchema, SortOrder
from ..enums import RegionCodeType


class RegionReadSchema(BaseSchema):
    id: int
    katotth_code: str
    name: str
    name_en: str
    code_type: RegionCodeType


class RegionFilterSchema(BaseFilterSchema):
    order_by: Literal["name"] = "name"
    order: SortOrder = SortOrder.ASC
