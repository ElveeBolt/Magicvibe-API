import secrets
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .core.database.alchemy.setup import async_session_factory
from .core.exceptions import UnauthorizedError
from .settings import settings
from .uow import UnitOfWork

security = HTTPBearer(auto_error=False)


async def require_service_token(
    auth: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> None:
    expected = settings.auth.service_token.get_secret_value().encode()
    provided = auth.credentials.encode() if auth else b""

    if not secrets.compare_digest(provided, expected):
        raise UnauthorizedError(headers={"WWW-Authenticate": "Bearer"})


def get_uow() -> UnitOfWork:
    return UnitOfWork(session_factory=async_session_factory)


UOWDep = Annotated[UnitOfWork, Depends(get_uow)]
