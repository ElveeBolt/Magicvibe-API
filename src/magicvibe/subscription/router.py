from typing import Annotated

from fastapi import APIRouter, Query, status

from ..core.schemas.base import PaginatedResponse
from .dependencies import SubscriptionServiceDep
from .schemas.subscription import (
    PlanReadSchema,
    SubscriptionCreateSchema,
    SubscriptionFilterSchema,
    SubscriptionReadSchema,
)

# No prefix: the domain serves `/subscriptions` and a user's `/plan`.
router = APIRouter()


@router.get(
    "/subscriptions",
    response_model=PaginatedResponse[SubscriptionReadSchema],
    tags=["subscriptions"],
)
async def get_subscriptions(
    service: SubscriptionServiceDep,
    filters: Annotated[SubscriptionFilterSchema, Query()],
):
    return await service.get_all(filters=filters)


@router.get(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionReadSchema,
    tags=["subscriptions"],
)
async def get_subscription(service: SubscriptionServiceDep, subscription_id: int):
    return await service.get(id_=subscription_id)


@router.post(
    "/subscriptions",
    response_model=SubscriptionReadSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["subscriptions"],
)
async def grant_premium(
    service: SubscriptionServiceDep, data: SubscriptionCreateSchema
):
    return await service.create(data=data)


@router.post(
    "/subscriptions/{subscription_id}/end",
    response_model=SubscriptionReadSchema,
    tags=["subscriptions"],
)
async def end_subscription(service: SubscriptionServiceDep, subscription_id: int):
    return await service.end(subscription_id=subscription_id)


@router.get("/users/{user_id}/plan", response_model=PlanReadSchema, tags=["users"])
async def get_user_plan(service: SubscriptionServiceDep, user_id: int):
    return await service.get_plan(user_id=user_id)
