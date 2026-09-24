from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from ...exceptions import NotFoundError
from ...generics import AbstractService
from ...schemas.base import BaseFilterSchema, PaginatedResponse

if TYPE_CHECKING:
    from .models import Base
    from .repository import AlchemyRepository
    from .uow import AlchemyUnitOfWork


class AlchemyService[
    CreateType: BaseModel,
    UpdateType: BaseModel,
    ReadType: BaseModel,
    FilterType: BaseFilterSchema,
    PkType: Any,
](AbstractService[CreateType, UpdateType, ReadType, FilterType, PkType], ABC):
    schema: type[ReadType]

    def __init__(self, uow: AlchemyUnitOfWork) -> None:
        self.uow = uow

    @property
    @abstractmethod
    def repository(self) -> AlchemyRepository[Base, PkType]:
        pass

    async def get(self, id_: PkType) -> ReadType:
        async with self.uow:
            entity = await self.repository.get(id_=id_)

            if entity is None:
                raise NotFoundError

            return self._to_schema(entity)

    async def get_all(self, filters: FilterType) -> PaginatedResponse[ReadType]:
        async with self.uow:
            filter_dict = filters.to_filter_dict()
            total = await self.repository.count(filters=filter_dict)
            results = await self.repository.get_all(
                filters=filter_dict,
                order_by=filters.order_by,
                descending=filters.descending,
                limit=filters.page_size,
                offset=filters.offset,
            )
            return PaginatedResponse.build(
                items=[self._to_schema(result) for result in results],
                total=total,
                filters=filters,
            )

    async def create(self, data: CreateType) -> ReadType:
        async with self.uow:
            entity = await self.repository.create(data.model_dump())
            return self._to_schema(entity)

    async def update(self, id_: PkType, data: UpdateType) -> ReadType:
        async with self.uow:
            update_data = data.model_dump(exclude_unset=True)

            if update_data:
                entity = await self.repository.update(id_=id_, data=update_data)
            else:
                entity = await self.repository.get(id_=id_)

            if entity is None:
                raise NotFoundError

            return self._to_schema(entity)

    async def delete(self, id_: PkType) -> None:
        async with self.uow:
            await self.repository.delete(id_=id_)

    async def exists(self, id_: PkType) -> bool:
        async with self.uow:
            return await self.repository.exists(id_=id_)

    def _to_schema(self, entity: Base) -> ReadType:
        return self.schema.model_validate(entity)
