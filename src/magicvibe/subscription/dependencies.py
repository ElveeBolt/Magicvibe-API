from typing import Annotated

from fastapi import Depends

from ..dependencies import UOWDep
from .services import SubscriptionService


async def get_subscription_service(uow: UOWDep) -> SubscriptionService:
    return SubscriptionService(uow)


SubscriptionServiceDep = Annotated[
    SubscriptionService, Depends(get_subscription_service)
]
