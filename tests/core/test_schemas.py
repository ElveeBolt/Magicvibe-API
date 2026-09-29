import pytest
from pydantic import ValidationError

from magicvibe.core.schemas.base import (
    BaseFilterSchema,
    BaseUpdateSchema,
    PaginatedResponse,
)
from magicvibe.core.schemas.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


def test_page_size_at_limit_is_accepted() -> None:
    filters = BaseFilterSchema.model_validate({"page_size": MAX_PAGE_SIZE})

    response = PaginatedResponse[int].build(items=[], total=0, filters=filters)

    assert filters.page_size == MAX_PAGE_SIZE
    assert response.page_size == MAX_PAGE_SIZE


@pytest.mark.parametrize("page_size", [0, MAX_PAGE_SIZE + 1])
def test_page_size_out_of_range_is_rejected(page_size: int) -> None:
    with pytest.raises(ValidationError) as error:
        BaseFilterSchema.model_validate({"page_size": page_size})

    assert [item["loc"] for item in error.value.errors()] == [("page_size",)]


def test_page_size_defaults_when_omitted() -> None:
    filters = BaseFilterSchema.model_validate({})

    assert filters.page_size == DEFAULT_PAGE_SIZE == 10


class _NameUpdateSchema(BaseUpdateSchema):
    name: str | None = None


def test_update_schema_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError) as error:
        _NameUpdateSchema.model_validate({"name": "Ann", "nickname": "A"})

    assert [(item["loc"], item["type"]) for item in error.value.errors()] == [
        (("nickname",), "extra_forbidden")
    ]


def test_update_schema_still_needs_a_field() -> None:
    with pytest.raises(ValidationError):
        _NameUpdateSchema.model_validate({})
