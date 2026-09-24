from typing import Annotated

from fastapi import Depends

from ..dependencies import UOWDep
from .services import BanService


async def get_ban_service(uow: UOWDep) -> BanService:
    return BanService(uow)


BanServiceDep = Annotated[BanService, Depends(get_ban_service)]
