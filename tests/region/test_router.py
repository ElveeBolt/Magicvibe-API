from typing import TYPE_CHECKING

from magicvibe.region.enums import RegionCodeType
from tests.factories import create_city, create_region

if TYPE_CHECKING:
    import httpx
    from sqlalchemy.ext.asyncio import AsyncSession


async def test_all_regions_on_one_page_sorted_by_name(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    for name in ("Черкаська", "Вінницька", "Київ"):
        await create_region(session, name=name)

    response = await client.get("/regions", params={"page_size": 100})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert [item["name"] for item in body["items"]] == [
        "Вінницька",
        "Київ",
        "Черкаська",
    ]


async def test_region_fields(client: httpx.AsyncClient, session: AsyncSession) -> None:
    region = await create_region(
        session,
        name="Київ",
        name_en="Kyiv",
        code_type=RegionCodeType.SPECIAL_STATUS_CITY,
    )

    response = await client.get("/regions")

    assert response.json()["items"] == [
        {
            "id": region.id,
            "katotth_code": region.katotth_code,
            "name": "Київ",
            "name_en": "Kyiv",
            "code_type": "K",
        }
    ]


async def test_cities_of_a_region(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    region = await create_region(session)
    other = await create_region(session)
    for name in ("Умань", "Черкаси", "Золотоноша"):
        await create_city(session, region, name=name)
    await create_city(session, other, name="Вінниця")

    response = await client.get(f"/regions/{region.id}/cities")

    assert response.status_code == 200
    items = response.json()["items"]
    assert {item["region_id"] for item in items} == {region.id}
    assert [item["name"] for item in items] == ["Золотоноша", "Умань", "Черкаси"]
    assert set(items[0]) == {"id", "region_id", "katotth_code", "name", "name_en"}


async def test_city_with_special_status(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    kyiv = await create_region(
        session, name="Київ", code_type=RegionCodeType.SPECIAL_STATUS_CITY
    )
    await create_city(session, kyiv, name="Київ")

    response = await client.get(f"/regions/{kyiv.id}/cities")

    assert [item["name"] for item in response.json()["items"]] == ["Київ"]


async def test_cities_of_an_unknown_region(client: httpx.AsyncClient) -> None:
    response = await client.get("/regions/999999/cities")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_page_size_above_the_limit(client: httpx.AsyncClient) -> None:
    response = await client.get("/regions", params={"page_size": 101})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
