from abc import ABC
from typing import TYPE_CHECKING, Any

from sqlalchemy import ColumnElement, Select, delete, exists, func, select
from sqlalchemy import update as update_sql

from ...generics.repository import AbstractRepository
from .models import Base

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


class AlchemyRepository[ModelType: Base, PkType](
    AbstractRepository[ModelType, PkType], ABC
):
    model: type[ModelType]

    def __init__(self, session: AsyncSession):
        if not hasattr(self, "model"):
            raise ValueError(
                f"Class {self.__class__.__name__} has no attribute 'model'"
            )

        self._session = session

    async def get(self, id_: PkType) -> ModelType | None:
        stmt = self._get_base_stmt().where(self.model.id == id_)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        descending: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> Sequence[ModelType]:
        stmt = self._get_base_stmt()
        conditions = self._build_conditions(filters)

        if conditions:
            stmt = stmt.where(*conditions)

        if order_by:
            if not hasattr(self.model, order_by):
                raise ValueError(
                    f"Unknown field for sorting: {order_by!r} in {self.model.__name__}"
                )

            column = getattr(self.model, order_by)
            stmt = stmt.order_by(column.desc() if descending else column.asc())

        if limit is not None:
            stmt = stmt.limit(limit)

        stmt = stmt.offset(offset)

        results = await self._session.execute(stmt)
        return results.scalars().all()

    async def create(self, data: dict[str, Any]) -> ModelType:
        entity = self.model(**data)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(self, id_: PkType, data: dict[str, Any]) -> ModelType | None:
        if not data:
            return await self.get(id_=id_)

        stmt = (
            update_sql(self.model)
            .where(self.model.id == id_)
            .values(**data)
            .returning(self.model.id)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()

        if result.scalar_one_or_none() is None:
            return None

        return await self.get(id_=id_)

    async def delete(self, id_: PkType) -> None:
        stmt = delete(self.model).where(self.model.id == id_)
        await self._session.execute(stmt)

    async def exists(self, id_: PkType) -> bool:
        stmt = select(exists().where(self.model.id == id_))
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def exists_by(self, filters: dict[str, Any]) -> bool:
        stmt = select(exists().where(*self._build_conditions(filters)))
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        stmt = select(func.count()).select_from(self.model)
        conditions = self._build_conditions(filters)

        if conditions:
            stmt = stmt.where(*conditions)

        result = await self._session.execute(stmt)
        return result.scalar_one()

    def _get_base_stmt(self) -> Select[tuple[ModelType]]:
        return select(self.model)

    def _build_conditions(
        self, filters: dict[str, Any] | None
    ) -> list[ColumnElement[bool]]:

        if not filters:
            return []

        unknown_fields = [key for key in filters if not hasattr(self.model, key)]

        if unknown_fields:
            raise ValueError(
                f"Unknown fields for filtering: {unknown_fields!r} "
                f"in {self.model.__name__}"
            )

        return [getattr(self.model, key) == value for key, value in filters.items()]
