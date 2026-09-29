from typing import TYPE_CHECKING

from magicvibe.report.enums import ReportReason
from magicvibe.report.schemas.report import ReportCreateSchema
from magicvibe.report.services import ReportService
from tests.factories import create_ban, create_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from magicvibe.uow import UnitOfWork


async def test_repeated_report_returns_the_open_one(
    uow: UnitOfWork, session: AsyncSession
) -> None:
    reporter = await create_user(session)
    target = await create_user(session)
    data = ReportCreateSchema(target_id=target.id, reason=ReportReason.SPAM)
    service = ReportService(uow)

    first, first_created = await service.create_by_reporter_id(reporter.id, data)
    second, second_created = await service.create_by_reporter_id(reporter.id, data)

    assert (first_created, second_created) == (True, False)
    assert second.id == first.id


async def test_report_against_a_banned_user_succeeds(
    uow: UnitOfWork, session: AsyncSession
) -> None:
    reporter = await create_user(session)
    target = await create_user(session)
    await create_ban(session, target)
    data = ReportCreateSchema(target_id=target.id, reason=ReportReason.OTHER)

    _, is_created = await ReportService(uow).create_by_reporter_id(reporter.id, data)

    assert is_created
