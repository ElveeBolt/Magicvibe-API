from typing import Annotated

from fastapi import APIRouter, Query, status

from ..core.schemas.base import PaginatedResponse
from ..user.dependencies import CurrentUserDep
from .dependencies import ReactionServiceDep
from .schemas.reaction import (
    LikerFilterSchema,
    LikerReadSchema,
    MatchFilterSchema,
    MatchReadSchema,
    ReactionCreateSchema,
    ReactionResultReadSchema,
)

# No prefix: the domain serves `/reactions`, `/matches` and `/likers`.
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


@router.get(
    "/likers", response_model=PaginatedResponse[LikerReadSchema], tags=["likers"]
)
async def get_likers(
    service: ReactionServiceDep,
    current_user: CurrentUserDep,
    filters: Annotated[LikerFilterSchema, Query()],
):
    """The "Who liked me" list of the acting user."""
    return await service.get_likers(user_id=current_user.id, filters=filters)
