from typing import Annotated

from fastapi import Depends

from ..dependencies import UOWDep
from .services import RegionService


async def get_region_service(uow: UOWDep) -> RegionService:
    return RegionService(uow)


RegionServiceDep = Annotated[RegionService, Depends(get_region_service)]
