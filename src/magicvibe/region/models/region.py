from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database.alchemy.models import Base
from ...core.database.alchemy.types import enum_type
from ..constants import KATOTTH_CODE_LENGTH, MAX_REGION_NAME_LENGTH
from ..enums import RegionCodeType


class Region(Base):
    """A region from KATOTTH. Filled only by the data loader; never deleted."""

    __tablename__ = "regions"

    katotth_code: Mapped[str] = mapped_column(String(KATOTTH_CODE_LENGTH), unique=True)
    name: Mapped[str] = mapped_column(String(MAX_REGION_NAME_LENGTH))
    name_en: Mapped[str] = mapped_column(String(MAX_REGION_NAME_LENGTH))
    code_type: Mapped[RegionCodeType] = mapped_column(
        enum_type(RegionCodeType, name="region_code_type_enum")
    )
