from enum import StrEnum

from sqlalchemy import Enum, MetaData


def enum_type[T: StrEnum](
    enum_cls: type[T], *, name: str, metadata: MetaData | None = None
) -> Enum:
    """Postgres enum backing `enum_cls`.

    Pass `metadata` when more than one column maps to the same type: it is then
    created with the schema itself instead of by whichever table happens to be
    created first, which a plain column reference (or an `ARRAY` of it) does not
    guarantee.
    """
    return Enum(
        enum_cls,
        name=name,
        metadata=metadata,
        values_callable=lambda enum: [member.value for member in enum],
    )
