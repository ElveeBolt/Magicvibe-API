from ..core.database.alchemy.repository import AlchemyRepository
from .models import Region, RegionCity


class RegionRepository(AlchemyRepository[Region, int]):
    model = Region


class RegionCityRepository(AlchemyRepository[RegionCity, int]):
    model = RegionCity
