from abc import ABC, abstractmethod


class AbstractUnitOfWork(ABC):
    """
    Abstract class for any units of work, which would
    be used for transaction atomicity.
    """

    async def __aenter__(self):
        """
        Enter the context manager for the Unit of Work.
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager for the Unit of Work.
        """
        try:
            if exc_type:
                await self.rollback()
            else:
                await self.commit()
        finally:
            await self.close()

    @abstractmethod
    async def commit(self):
        """
        Persist all changes made during the Unit of Work
        into the database (or another storage). This should
        be called only if no errors occurred in the block.
        """
        ...

    @abstractmethod
    async def rollback(self):
        """
        Revert all uncommitted changes made during the Unit of Work.
        Called automatically if an error occurred inside the block.
        """
        ...

    @abstractmethod
    async def close(self):
        """
        Close the Unit of Work, if possible.
        """
        ...
