from typing import TYPE_CHECKING

import pytest

from magicvibe.core.exceptions import ErrorCode, NotFoundError
from magicvibe.region.schemas.region import RegionFilterSchema
from magicvibe.region.schemas.region_city import RegionCityFilterSchema
from magicvibe.region.services import RegionService
from tests.factories import create_city, create_region

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from magicvibe.uow import UnitOfWork


async def test_regions_are_paginated(uow: UnitOfWork, session: AsyncSession) -> None:
    for name in ("Волинська", "Житомирська", "Сумська"):
        await create_region(session, name=name)

    page = await RegionService(uow).list_regions(
        RegionFilterSchema(page=2, page_size=2)
    )

    assert [region.name for region in page.items] == ["Сумська"]
    assert (page.total, page.pages) == (3, 2)


async def test_cities_only_of_the_region(
    uow: UnitOfWork, session: AsyncSession
) -> None:
    region = await create_region(session)
    other = await create_region(session)
    city = await create_city(session, region)
    await create_city(session, other)

    page = await RegionService(uow).list_cities(region.id, RegionCityFilterSchema())

    assert [item.id for item in page.items] == [city.id]


async def test_cities_of_an_unknown_region(uow: UnitOfWork) -> None:
    with pytest.raises(NotFoundError) as error:
        await RegionService(uow).list_cities(999_999, RegionCityFilterSchema())

    assert error.value.code is ErrorCode.NOT_FOUND
