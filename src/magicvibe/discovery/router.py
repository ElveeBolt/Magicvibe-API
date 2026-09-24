from fastapi import APIRouter

from ..user.dependencies import CurrentUserDep
from .dependencies import DiscoveryServiceDep
from .schemas.candidate import NextCandidateSchema

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.get("/next", response_model=NextCandidateSchema)
async def get_next_candidate(
    service: DiscoveryServiceDep, current_user: CurrentUserDep
):
    # The acting user arrives with their profile and criteria already loaded,
    # so both sides of the search cost no extra query.
    return await service.get_next_candidate(viewer=current_user)
