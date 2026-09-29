from enum import StrEnum


class RegionCodeType(StrEnum):
    """KATOTTH category of a region."""

    OBLAST = "O"  # an oblast or the Autonomous Republic of Crimea
    SPECIAL_STATUS_CITY = "K"  # Kyiv, Sevastopol
