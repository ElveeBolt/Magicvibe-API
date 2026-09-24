from typing import Annotated

from fastapi import APIRouter, Query, status

from ..core.schemas.base import PaginatedResponse
from .dependencies import BanServiceDep
from .schemas.ban import (
    BanCreateSchema,
    BanFilterSchema,
    BanLiftSchema,
    BanReadSchema,
    BanUpdateSchema,
)

router = APIRouter(prefix="/bans", tags=["bans"])


@router.get("", response_model=PaginatedResponse[BanReadSchema])
async def get_bans(
    service: BanServiceDep, filters: Annotated[BanFilterSchema, Query()]
):
    return await service.get_all(filters=filters)


@router.get("/{ban_id}", response_model=BanReadSchema)
async def get_ban(service: BanServiceDep, ban_id: int):
    return await service.get(id_=ban_id)


@router.post("", response_model=BanReadSchema, status_code=status.HTTP_201_CREATED)
async def create_ban(service: BanServiceDep, data: BanCreateSchema):
    return await service.create(data=data)


@router.patch("/{ban_id}", response_model=BanReadSchema)
async def update_ban(service: BanServiceDep, ban_id: int, data: BanUpdateSchema):
    return await service.update(id_=ban_id, data=data)


@router.post("/{ban_id}/lift", response_model=BanReadSchema)
async def lift_ban(service: BanServiceDep, ban_id: int, data: BanLiftSchema):
    return await service.lift(ban_id=ban_id, data=data)
