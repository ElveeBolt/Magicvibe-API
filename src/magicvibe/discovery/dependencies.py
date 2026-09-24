from typing import Annotated

from fastapi import Depends

from ..dependencies import UOWDep
from .services import DiscoveryService


async def get_discovery_service(uow: UOWDep) -> DiscoveryService:
    return DiscoveryService(uow)


DiscoveryServiceDep = Annotated[DiscoveryService, Depends(get_discovery_service)]
