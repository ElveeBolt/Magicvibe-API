from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database.alchemy.models import Base
from ..constants import KATOTTH_CODE_LENGTH, MAX_REGION_NAME_LENGTH


class RegionCity(Base):
    """A city from KATOTTH within its region. Filled only by the data loader;
    never deleted, so the foreign key has no `ON DELETE` action."""

    __tablename__ = "cities"

    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"))
    katotth_code: Mapped[str] = mapped_column(String(KATOTTH_CODE_LENGTH), unique=True)
    name: Mapped[str] = mapped_column(String(MAX_REGION_NAME_LENGTH))
    name_en: Mapped[str] = mapped_column(String(MAX_REGION_NAME_LENGTH))

    __table_args__ = (Index(None, region_id),)
