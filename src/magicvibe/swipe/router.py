from typing import Annotated

from fastapi import APIRouter, Query, status

from ..core.schemas.base import PaginatedResponse
from ..user.dependencies import CurrentUserDep
from .dependencies import SwipeServiceDep
from .schemas.swipe import (
    MatchFilterSchema,
    MatchReadSchema,
    SwipeCreateSchema,
    SwipeResultReadSchema,
)

# No prefix: the domain serves two resources, `/swipes` and `/matches`.
router = APIRouter()


@router.post(
    "/swipes",
    response_model=SwipeResultReadSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["swipes"],
)
async def create_swipe(
    service: SwipeServiceDep, current_user: CurrentUserDep, data: SwipeCreateSchema
):
    return await service.create(user_id=current_user.id, data=data)


@router.get(
    "/matches", response_model=PaginatedResponse[MatchReadSchema], tags=["matches"]
)
async def get_matches(
    service: SwipeServiceDep,
    current_user: CurrentUserDep,
    filters: Annotated[MatchFilterSchema, Query()],
):
    return await service.get_matches(user_id=current_user.id, filters=filters)
