from typing import Annotated

from fastapi import Depends

from ..dependencies import UOWDep
from .services import SwipeService


async def get_swipe_service(uow: UOWDep) -> SwipeService:
    return SwipeService(uow)


SwipeServiceDep = Annotated[SwipeService, Depends(get_swipe_service)]
