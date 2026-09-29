import pytest
from pydantic import ValidationError

from magicvibe.core.schemas.base import BaseFilterSchema, PaginatedResponse
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
