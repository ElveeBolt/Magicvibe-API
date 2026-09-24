from typing import TYPE_CHECKING

from ...generics import AbstractUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class AlchemyUnitOfWork(AbstractUnitOfWork):
    """
    Unit of Work implementation for SQLAlchemy AsyncSession.
    Provides transaction management (commit / rollback) and
    access to repositories within the same session.
    """

    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    async def __aenter__(self):
        self._session = self._session_factory()
        return await super().__aenter__()

    async def commit(self):
        await self._session.commit()

    async def close(self):
        await self._session.close()

    async def rollback(self):
        await self._session.rollback()
