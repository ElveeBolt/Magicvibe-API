from fastapi import APIRouter

from ..user.dependencies import CurrentUserDep
from ..user.schemas.user import UserPublicSchema
from .dependencies import DiscoveryServiceDep

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.get(
    "/next",
    response_model=UserPublicSchema | None,
    responses={200: {"description": "The next profile, or `null` when nobody is left"}},
)
async def get_next_candidate(
    service: DiscoveryServiceDep, current_user: CurrentUserDep
):
    # The acting user arrives with their profile and preferences already
    # loaded, so both sides of the search cost no extra query.
    return await service.get_next_candidate(viewer=current_user)
