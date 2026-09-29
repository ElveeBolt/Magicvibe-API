from typing import Annotated

from fastapi import APIRouter, Query, status

from ..core.schemas.base import PaginatedResponse
from ..user.dependencies import CurrentUserDep
from .dependencies import ReactionServiceDep
from .schemas.reaction import (
    MatchFilterSchema,
    MatchReadSchema,
    ReactionCreateSchema,
    ReactionResultReadSchema,
)

# No prefix: the domain serves two resources, `/reactions` and `/matches`.
router = APIRouter()


@router.post(
    "/reactions",
    response_model=ReactionResultReadSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["reactions"],
)
async def create_reaction(
    service: ReactionServiceDep,
    current_user: CurrentUserDep,
    data: ReactionCreateSchema,
):
    return await service.create(user_id=current_user.id, data=data)


@router.get(
    "/matches", response_model=PaginatedResponse[MatchReadSchema], tags=["matches"]
)
async def get_matches(
    service: ReactionServiceDep,
    current_user: CurrentUserDep,
    filters: Annotated[MatchFilterSchema, Query()],
):
    return await service.get_matches(user_id=current_user.id, filters=filters)
