import asyncio
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import func, select

from magicvibe.report.enums import ReportStatus
from magicvibe.report.models import Report
from tests.conftest import acting_user
from tests.factories import create_ban, create_report, create_user

if TYPE_CHECKING:
    import httpx
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from magicvibe.user.models import User


def headers_of(user: User) -> dict[str, str]:
    assert user.telegram is not None
    return acting_user(user.telegram.telegram_id)


def report_of(target: User) -> dict[str, object]:
    return {"target_id": target.id, "reason": "spam"}


async def open_reports(session: AsyncSession, reporter: User, target: User) -> int:
    return (
        await session.scalar(
            select(func.count())
            .select_from(Report)
            .where(
                Report.reporter_id == reporter.id,
                Report.target_id == target.id,
                Report.status == ReportStatus.OPEN,
            )
        )
        or 0
    )


async def test_first_report(client: httpx.AsyncClient, session: AsyncSession) -> None:
    reporter = await create_user(session)
    target = await create_user(session)

    response = await client.post(
        "/reports", json=report_of(target), headers=headers_of(reporter)
    )

    assert response.status_code == 201
    assert response.json()["status"] == "open"
    assert response.json()["reporter_id"] == reporter.id


async def test_repeated_report_while_open(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    reporter = await create_user(session)
    target = await create_user(session)
    first = await client.post(
        "/reports", json=report_of(target), headers=headers_of(reporter)
    )

    again = await client.post(
        "/reports",
        json={"target_id": target.id, "reason": "scam", "comment": "Again"},
        headers=headers_of(reporter),
    )

    assert again.status_code == 200
    assert again.json()["id"] == first.json()["id"]
    assert await open_reports(session, reporter, target) == 1


async def test_report_after_review(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    reporter = await create_user(session)
    target = await create_user(session)
    await create_report(session, reporter, target, status=ReportStatus.RESOLVED)

    response = await client.post(
        "/reports", json=report_of(target), headers=headers_of(reporter)
    )

    assert response.status_code == 201
    assert response.json()["status"] == "open"


async def test_reporting_a_banned_user(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    reporter = await create_user(session)
    target = await create_user(session)
    await create_ban(session, target)

    response = await client.post(
        "/reports", json=report_of(target), headers=headers_of(reporter)
    )

    assert response.status_code == 201


async def test_reporting_oneself(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    reporter = await create_user(session)

    response = await client.post(
        "/reports", json=report_of(reporter), headers=headers_of(reporter)
    )

    assert response.status_code == 400
    assert response.json()["code"] == "SELF_ACTION"


async def test_unknown_target(client: httpx.AsyncClient, session: AsyncSession) -> None:
    reporter = await create_user(session)

    response = await client.post(
        "/reports",
        json={"target_id": 999_999, "reason": "spam"},
        headers=headers_of(reporter),
    )

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


@pytest.mark.concurrency
async def test_simultaneous_repeated_reports(
    concurrent_client: httpx.AsyncClient,
    committed_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with committed_session_factory() as session:
        reporter = await create_user(session)
        target = await create_user(session)

    responses = await asyncio.gather(
        *(
            concurrent_client.post(
                "/reports", json=report_of(target), headers=headers_of(reporter)
            )
            for _ in range(2)
        )
    )

    assert sorted(r.status_code for r in responses) == [200, 201]
    assert len({r.json()["id"] for r in responses}) == 1
    async with committed_session_factory() as session:
        assert await open_reports(session, reporter, target) == 1


async def test_resolve_a_report(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    report = await create_report(
        session, await create_user(session), await create_user(session)
    )

    response = await client.patch(f"/reports/{report.id}", json={"status": "resolved"})

    assert response.status_code == 200
    assert response.json()["status"] == "resolved"


@pytest.mark.parametrize("status", ["dismissed", "resolved"])
async def test_review_statuses_are_accepted(
    client: httpx.AsyncClient, session: AsyncSession, status: str
) -> None:
    report = await create_report(
        session, await create_user(session), await create_user(session)
    )

    response = await client.patch(f"/reports/{report.id}", json={"status": status})

    assert response.status_code == 200


async def test_reopen_a_report(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    report = await create_report(
        session,
        await create_user(session),
        await create_user(session),
        status=ReportStatus.RESOLVED,
    )

    response = await client.patch(f"/reports/{report.id}", json={"status": "open"})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert [e["field"] for e in response.json()["errors"]] == ["status"]


async def test_review_unknown_report(client: httpx.AsyncClient) -> None:
    response = await client.patch("/reports/999999", json={"status": "resolved"})

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_review_with_an_unknown_field(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    report = await create_report(
        session, await create_user(session), await create_user(session)
    )

    response = await client.patch(
        f"/reports/{report.id}", json={"status": "resolved", "note": "x"}
    )

    assert response.status_code == 400
    assert [(e["field"], e["type"]) for e in response.json()["errors"]] == [
        ("note", "extra_forbidden")
    ]
    assert (await client.get(f"/reports/{report.id}")).json()["status"] == "open"
