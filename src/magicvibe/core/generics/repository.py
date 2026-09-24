from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence


class AbstractRepository[ModelType, PkType](ABC):
    @abstractmethod
    async def get(self, id_: PkType) -> ModelType | None:
        """Get entity by id."""
        ...

    @abstractmethod
    async def get_all(
        self,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        descending: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> Sequence[ModelType]:
        """Get all entities by some filters and offset."""
        ...

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> ModelType:
        """Create a new entity to the repository."""
        ...

    @abstractmethod
    async def update(self, id_: PkType, data: dict[str, Any]) -> ModelType | None:
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

    @abstractmethod
    async def exists_by(self, filters: dict[str, Any]) -> bool:
        """Check if any entity matches the filters."""
        ...

    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Return the number of entities in the repository."""
        ...
