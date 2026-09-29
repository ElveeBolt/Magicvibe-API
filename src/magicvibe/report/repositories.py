from typing import Any

from sqlalchemy.dialects.postgresql import insert

from ..core.database.alchemy.repository import AlchemyRepository
from .enums import ReportStatus
from .models import Report


class ReportRepository(AlchemyRepository[Report, int]):
    model = Report

    async def create_if_no_open(self, data: dict[str, Any]) -> Report | None:
        """Inserts an open report, or nothing when the reporter already has an
        open report against the target (the partial unique index decides)."""
        stmt = (
            insert(Report)
            .values(**data)
            .on_conflict_do_nothing(
                index_elements=[Report.reporter_id, Report.target_id],
                index_where=Report.status == ReportStatus.OPEN,
            )
            .returning(Report)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_open(self, reporter_id: int, target_id: int) -> Report | None:
        stmt = self._get_base_stmt().where(
            Report.reporter_id == reporter_id,
            Report.target_id == target_id,
            Report.status == ReportStatus.OPEN,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
