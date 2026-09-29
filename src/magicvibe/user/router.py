from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from ..core.schemas.base import PaginatedResponse
from .dependencies import UserServiceDep
from .schemas.user import (
    UserCreateSchema,
    UserFilterSchema,
    UserReadSchema,
)
from .schemas.user_preference import (
    UserPreferenceCreateSchema,
    UserPreferenceReadSchema,
    UserPreferenceUpdateSchema,
)
from .schemas.user_profile import (
    UserProfileCreateSchema,
    UserProfileReadSchema,
    UserProfileUpdateSchema,
)
from .schemas.user_telegram import UserTelegramReadSchema, UserTelegramUpdateSchema

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserReadSchema)
async def get_user(service: UserServiceDep, user_id: int):
    return await service.get(id_=user_id)


@router.get("", response_model=PaginatedResponse[UserReadSchema])
async def get_users(
    service: UserServiceDep, filters: Annotated[UserFilterSchema, Query()]
):
    return await service.get_all(filters=filters)


@router.post(
    "",
    response_model=UserReadSchema,
    responses={
        status.HTTP_200_OK: {"description": "Existing user refreshed"},
        status.HTTP_201_CREATED: {
            "model": UserReadSchema,
            "description": "New user registered",
        },
    },
)
async def upsert_user(
    service: UserServiceDep, data: UserCreateSchema, response: Response
):
    user, is_created = await service.upsert(data=data)
    response.status_code = status.HTTP_201_CREATED if is_created else status.HTTP_200_OK
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(service: UserServiceDep, user_id: int):
    return await service.delete(id_=user_id)


@router.get("/{user_id}/profile", response_model=UserProfileReadSchema)
async def get_profile(service: UserServiceDep, user_id: int):
    return await service.get_profile(user_id=user_id)


@router.put("/{user_id}/profile", response_model=UserProfileReadSchema)
async def set_profile(
    service: UserServiceDep, user_id: int, data: UserProfileCreateSchema
):
    return await service.set_profile(user_id=user_id, data=data)


@router.patch("/{user_id}/profile", response_model=UserProfileReadSchema)
async def update_user_profile(
    service: UserServiceDep, user_id: int, data: UserProfileUpdateSchema
):
    return await service.update_profile(user_id=user_id, data=data)


@router.get("/{user_id}/preferences", response_model=UserPreferenceReadSchema)
async def get_preferences(service: UserServiceDep, user_id: int):
    return await service.get_preference(user_id=user_id)


@router.put("/{user_id}/preferences", response_model=UserPreferenceReadSchema)
async def set_preferences(
    service: UserServiceDep, user_id: int, data: UserPreferenceCreateSchema
):
    return await service.set_preference(user_id=user_id, data=data)


@router.patch("/{user_id}/preferences", response_model=UserPreferenceReadSchema)
async def update_preferences(
    service: UserServiceDep, user_id: int, data: UserPreferenceUpdateSchema
):
    return await service.update_preference(user_id=user_id, data=data)


@router.get("/{user_id}/telegram", response_model=UserTelegramReadSchema)
async def get_user_telegram(service: UserServiceDep, user_id: int):
    return await service.get_telegram(user_id=user_id)


@router.patch("/{user_id}/telegram", response_model=UserTelegramReadSchema)
async def update_user_telegram(
    service: UserServiceDep, user_id: int, data: UserTelegramUpdateSchema
):
    return await service.update_telegram(user_id=user_id, data=data)
