from typing import TYPE_CHECKING

import pytest
from sqlalchemy.exc import IntegrityError

from magicvibe.exceptions import constraint_name
from magicvibe.report.enums import ReportStatus
from tests.factories import create_report, create_user

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def test_report_of_oneself_is_rejected(session: AsyncSession) -> None:
    user = await create_user(session)

    with pytest.raises(IntegrityError) as error:
        await create_report(session, user, user)

    assert constraint_name(error.value) == "ck_reports_not_self"


async def test_one_open_report_per_reporter_and_target(session: AsyncSession) -> None:
    reporter = await create_user(session)
    target = await create_user(session)
    await create_report(session, reporter, target)

    with pytest.raises(IntegrityError) as error:
        await create_report(session, reporter, target)

    assert constraint_name(error.value) == "ix_reports_reporter_id_target_id"


async def test_closed_reports_do_not_count(session: AsyncSession) -> None:
    reporter = await create_user(session)
    target = await create_user(session)

    for status in (ReportStatus.RESOLVED, ReportStatus.DISMISSED, ReportStatus.OPEN):
        await create_report(session, reporter, target, status=status)
