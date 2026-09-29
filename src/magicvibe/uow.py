from .ban.repositories import BanRepository
from .core.database.alchemy.uow import AlchemyUnitOfWork
from .discovery.repositories import DiscoveryRepository
from .reaction.repositories import ReactionRepository
from .report.repositories import ReportRepository
from .user.repositories import UserRepository


class UnitOfWork(AlchemyUnitOfWork):
    user: UserRepository
    reaction: ReactionRepository
    discovery: DiscoveryRepository
    report: ReportRepository
    ban: BanRepository

    async def __aenter__(self):
        await super().__aenter__()

        self.user = UserRepository(self._session)
        self.reaction = ReactionRepository(self._session)
        self.discovery = DiscoveryRepository(self._session)
        self.report = ReportRepository(self._session)
        self.ban = BanRepository(self._session)

        return self
