from typing import TYPE_CHECKING

import pytest
from sqlalchemy.exc import IntegrityError

from magicvibe.exceptions import constraint_name
from magicvibe.region.enums import RegionCodeType
from magicvibe.region.models import Region, RegionCity
from tests.factories import create_region

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def test_region_code_is_unique(session: AsyncSession) -> None:
    region = await create_region(session)
    session.add(
        Region(
            katotth_code=region.katotth_code,
            name="Інша",
            name_en="Insha",
            code_type=RegionCodeType.OBLAST,
        )
    )

    with pytest.raises(IntegrityError) as error:
        await session.flush()

    assert constraint_name(error.value) == "uq_regions_katotth_code"


async def test_city_code_is_unique(session: AsyncSession) -> None:
    region = await create_region(session)
    for _ in range(2):
        session.add(
            RegionCity(
                region_id=region.id,
                katotth_code="UA00000000000000001",
                name="Місто",
                name_en="Misto",
            )
        )

    with pytest.raises(IntegrityError) as error:
        await session.flush()

    assert constraint_name(error.value) == "uq_cities_katotth_code"


async def test_city_needs_an_existing_region(session: AsyncSession) -> None:
    session.add(
        RegionCity(
            region_id=999_999,
            katotth_code="UA00000000000000002",
            name="Місто",
            name_en="Misto",
        )
    )

    with pytest.raises(IntegrityError) as error:
        await session.flush()

    assert constraint_name(error.value) == "fk_cities_region_id_regions"
