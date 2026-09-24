from typing import Annotated

from fastapi import APIRouter, Query, status

from ..core.schemas.base import PaginatedResponse
from ..user.dependencies import CurrentUserDep
from .dependencies import ReportServiceDep
from .schemas.report import (
    ReportCreateSchema,
    ReportFilterSchema,
    ReportReadSchema,
    ReportUpdateSchema,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=PaginatedResponse[ReportReadSchema])
async def get_reports(
    service: ReportServiceDep, filters: Annotated[ReportFilterSchema, Query()]
):
    return await service.get_all(filters=filters)


@router.get("/{report_id}", response_model=ReportReadSchema)
async def get_report(service: ReportServiceDep, report_id: int):
    return await service.get(id_=report_id)


@router.post("", response_model=ReportReadSchema, status_code=status.HTTP_201_CREATED)
async def create_report(
    service: ReportServiceDep, current_user: CurrentUserDep, data: ReportCreateSchema
):
    return await service.create_by_reporter_id(reporter_id=current_user.id, data=data)


@router.patch("/{report_id}", response_model=ReportReadSchema)
async def update_report(
    service: ReportServiceDep, report_id: int, data: ReportUpdateSchema
):
    return await service.update(id_=report_id, data=data)
