from .ban.repositories import BanRepository
from .core.database.alchemy.uow import AlchemyUnitOfWork
from .discovery.repositories import DiscoveryRepository
from .reaction.repositories import MatchRepository, ReactionRepository
from .region.repositories import RegionCityRepository, RegionRepository
from .report.repositories import ReportRepository
from .subscription.repositories import SubscriptionRepository
from .user.repositories import UserRepository


class UnitOfWork(AlchemyUnitOfWork):
    user: UserRepository
    reaction: ReactionRepository
    match: MatchRepository
    region: RegionRepository
    region_city: RegionCityRepository
    discovery: DiscoveryRepository
    report: ReportRepository
    subscription: SubscriptionRepository
    ban: BanRepository

    async def __aenter__(self):
        await super().__aenter__()

        self.user = UserRepository(self._session)
        self.reaction = ReactionRepository(self._session)
        self.match = MatchRepository(self._session)
        self.region = RegionRepository(self._session)
        self.region_city = RegionCityRepository(self._session)
        self.discovery = DiscoveryRepository(self._session)
        self.report = ReportRepository(self._session)
        self.subscription = SubscriptionRepository(self._session)
        self.ban = BanRepository(self._session)

        return self
