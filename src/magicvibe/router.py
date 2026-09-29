from fastapi import APIRouter, Depends

from .ban.router import router as ban_router
from .dependencies import require_service_token
from .discovery.router import router as discovery_router
from .reaction.router import router as reaction_router
from .region.router import router as region_router
from .report.router import router as report_router
from .subscription.router import router as subscription_router
from .user.router import router as user_router

bot_router = APIRouter(dependencies=[Depends(require_service_token)])

bot_router.include_router(user_router)
bot_router.include_router(reaction_router)
bot_router.include_router(region_router)
bot_router.include_router(discovery_router)
bot_router.include_router(report_router)
bot_router.include_router(subscription_router)
bot_router.include_router(ban_router)
