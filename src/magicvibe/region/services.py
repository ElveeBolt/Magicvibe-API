from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from ..core.exceptions import NotFoundError
from ..core.schemas.base import BaseFilterSchema, PaginatedResponse
from .schemas.region import RegionFilterSchema, RegionReadSchema
from .schemas.region_city import RegionCityFilterSchema, RegionCityReadSchema

if TYPE_CHECKING:
    from ..core.database.alchemy.repository import AlchemyRepository
    from ..uow import UnitOfWork


class RegionService:
    """Read-only lookups for the two-step city choice: a region, then a city."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def list_regions(
        self, filters: RegionFilterSchema
    ) -> PaginatedResponse[RegionReadSchema]:
        async with self.uow:
            return await self._page(
                self.uow.region, RegionReadSchema, filters, conditions={}
            )

    async def list_cities(
        self, region_id: int, filters: RegionCityFilterSchema
    ) -> PaginatedResponse[RegionCityReadSchema]:
        async with self.uow:
            if not await self.uow.region.exists(id_=region_id):
                raise NotFoundError("Region not found")

            return await self._page(
                self.uow.region_city,
                RegionCityReadSchema,
                filters,
                conditions={"region_id": region_id},
            )

    @staticmethod
    async def _page[ReadType: BaseModel](
        repository: AlchemyRepository[Any, int],
        schema: type[ReadType],
        filters: BaseFilterSchema,
        conditions: dict[str, Any],
    ) -> PaginatedResponse[ReadType]:
        total = await repository.count(filters=conditions)
        rows = await repository.get_all(
            filters=conditions,
            order_by=filters.order_by,
            descending=filters.descending,
            limit=filters.page_size,
            offset=filters.offset,
        )
        return PaginatedResponse.build(
            items=[schema.model_validate(row) for row in rows],
            total=total,
            filters=filters,
        )
