from typing import Annotated

from pydantic import StringConstraints

from ..constants import MAX_COMMENT_LENGTH

type Comment = Annotated[
    str,
    StringConstraints(
        min_length=1, max_length=MAX_COMMENT_LENGTH, strip_whitespace=True
    ),
]
