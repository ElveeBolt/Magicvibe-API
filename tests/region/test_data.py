"""The KATOTTH data file in data/regions/ must fit the region models exactly, so
the loader can insert it as it is."""

import json
import re
from pathlib import Path
from typing import Any

import pytest

from magicvibe.region.constants import KATOTTH_CODE_LENGTH, MAX_REGION_NAME_LENGTH
from magicvibe.region.enums import RegionCodeType

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "regions"
DATA_FILES = sorted(DATA_DIR.glob("katotth_*.json"))

REGION_FIELDS = {"katotth_code", "name", "name_en", "code_type", "cities"}
CITY_FIELDS = {"katotth_code", "name", "name_en"}
CODE = re.compile(r"UA\d{17}")


def load(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_there_is_a_data_file() -> None:
    assert DATA_FILES
    for path in DATA_FILES:
        assert re.fullmatch(r"katotth_\d{4}-\d{2}-\d{2}\.json", path.name)


@pytest.mark.parametrize("path", DATA_FILES, ids=lambda p: p.name)
def test_file_matches_the_models(path: Path) -> None:
    regions = load(path)
    cities = [city for region in regions for city in region["cities"]]

    for region in regions:
        assert set(region) == REGION_FIELDS
        assert region["code_type"] in {member.value for member in RegionCodeType}
    for item in [*regions, *cities]:
        assert len(item["katotth_code"]) == KATOTTH_CODE_LENGTH
        assert CODE.fullmatch(item["katotth_code"])
        assert 0 < len(item["name"]) <= MAX_REGION_NAME_LENGTH
        assert 0 < len(item["name_en"]) <= MAX_REGION_NAME_LENGTH
        assert item["name_en"].isascii()
    for city in cities:
        assert set(city) == CITY_FIELDS

    region_codes = [region["katotth_code"] for region in regions]
    city_codes = [city["katotth_code"] for city in cities]
    assert len(set(region_codes)) == len(region_codes)
    assert len(set(city_codes)) == len(city_codes)


@pytest.mark.parametrize("path", DATA_FILES, ids=lambda p: p.name)
def test_special_status_regions_have_one_city_of_their_own(path: Path) -> None:
    special = [
        region
        for region in load(path)
        if region["code_type"] == RegionCodeType.SPECIAL_STATUS_CITY
    ]

    assert {region["name"] for region in special} == {"Київ", "Севастополь"}
    for region in special:
        assert [city["name"] for city in region["cities"]] == [region["name"]]
