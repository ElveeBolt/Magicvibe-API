from typing import Annotated

from fastapi import APIRouter, Query

from ..core.schemas.base import PaginatedResponse
from .dependencies import RegionServiceDep
from .schemas.region import RegionFilterSchema, RegionReadSchema
from .schemas.region_city import RegionCityFilterSchema, RegionCityReadSchema

router = APIRouter(prefix="/regions", tags=["regions"])


@router.get("", response_model=PaginatedResponse[RegionReadSchema])
async def get_regions(
    service: RegionServiceDep, filters: Annotated[RegionFilterSchema, Query()]
):
    return await service.list_regions(filters=filters)


@router.get(
    "/{region_id}/cities", response_model=PaginatedResponse[RegionCityReadSchema]
)
async def get_region_cities(
    service: RegionServiceDep,
    region_id: int,
    filters: Annotated[RegionCityFilterSchema, Query()],
):
    return await service.list_cities(region_id=region_id, filters=filters)
