from ..core.database.alchemy.repository import AlchemyRepository
from .models import Report


class ReportRepository(AlchemyRepository[Report, int]):
    model = Report
