from typing import TYPE_CHECKING

from ..core.database.alchemy.service import AlchemyService
from ..core.exceptions import BadRequestError, ErrorCode, NotFoundError
from .schemas.report import (
    ReportCreateSchema,
    ReportFilterSchema,
    ReportReadSchema,
    ReportUpdateSchema,
)

if TYPE_CHECKING:
    from ..uow import UnitOfWork
    from .repositories import ReportRepository


class ReportService(
    AlchemyService[
        ReportCreateSchema,
        ReportUpdateSchema,
        ReportReadSchema,
        ReportFilterSchema,
        int,
    ]
):
    schema = ReportReadSchema
    uow: UnitOfWork

    @property
    def repository(self) -> ReportRepository:  # type: ignore[override]
        return self.uow.report

    async def create_by_reporter_id(
        self, reporter_id: int, data: ReportCreateSchema
    ) -> ReportReadSchema:
        if reporter_id == data.target_id:
            raise BadRequestError(
                "A user cannot report themselves", code=ErrorCode.SELF_ACTION
            )

        async with self.uow:
            if not await self.uow.user.exists(id_=data.target_id):
                raise NotFoundError("Target user not found")

            report = await self.repository.create(
                {**data.model_dump(), "reporter_id": reporter_id}
            )
            return self._to_schema(report)
