from typing import Any

from pydantic import BeforeValidator


def not_none(v: Any) -> Any:
    """Raise ValueError if the value is explicitly None."""
    if v is None:
        raise ValueError("This field cannot be set to null")
    return v


NonNullable = BeforeValidator(not_none)
