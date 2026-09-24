from typing import Annotated

from fastapi import Depends

from ..dependencies import UOWDep
from .services import ReportService


async def get_report_service(uow: UOWDep) -> ReportService:
    return ReportService(uow)


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
