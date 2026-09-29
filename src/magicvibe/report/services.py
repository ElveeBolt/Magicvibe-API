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
    ) -> tuple[ReportReadSchema, bool]:
        """Files a report; while the reporter's earlier report against the
        same target is open, returns that one instead of a second."""
        if reporter_id == data.target_id:
            raise BadRequestError(
                "A user cannot report themselves", code=ErrorCode.SELF_ACTION
            )

        async with self.uow:
            if not await self.uow.user.exists(id_=data.target_id):
                raise NotFoundError("Target user not found")

            values = {**data.model_dump(), "reporter_id": reporter_id}

            # The open report that blocked the insert may be closed before it
            # is read; then the insert is simply tried again.
            while True:
                report = await self.repository.create_if_no_open(values)

                if report is not None:
                    return self._to_schema(report), True

                existing = await self.repository.get_open(reporter_id, data.target_id)

                if existing is not None:
                    return self._to_schema(existing), False
