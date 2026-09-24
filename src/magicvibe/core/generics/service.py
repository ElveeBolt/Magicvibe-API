from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..schemas.base import PaginatedResponse


class AbstractService[CreateType, UpdateType, ReadType, FilterType, PkType](ABC):
    """
    Abstract base class defining the interface for a CRUD service.

    This class is designed to outline a contract for CRUD operations,
    which should be implemented by any subclass. It enforces the implementation
    of asynchronous methods adhering to this interface, thus ensuring a consistent
    structure for derived services.
    """

    @abstractmethod
    async def get(self, id_: PkType) -> ReadType | None:
        """Get entity by id."""
        ...

    @abstractmethod
    async def get_all(self, filters: FilterType) -> PaginatedResponse[ReadType]:
        """Get all entities by some filters."""
        ...

    @abstractmethod
    async def create(self, data: CreateType) -> ReadType:
        """Create a new entity."""
        ...

    @abstractmethod
    async def update(self, id_: PkType, data: UpdateType) -> ReadType:
        """Update an existing entity by id."""
        ...

    @abstractmethod
    async def delete(self, id_: PkType) -> None:
        """Delete an entity by id."""
        ...

    @abstractmethod
    async def exists(self, id_: PkType) -> bool:
        """Check if an entity exists in the repository."""
        ...
