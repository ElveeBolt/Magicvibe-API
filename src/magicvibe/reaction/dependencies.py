from typing import Annotated

from fastapi import Depends

from ..dependencies import UOWDep
from .services import ReactionService


async def get_reaction_service(uow: UOWDep) -> ReactionService:
    return ReactionService(uow)


ReactionServiceDep = Annotated[ReactionService, Depends(get_reaction_service)]
