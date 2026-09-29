# Tasks

## 1. Page size limit in the shared filter schema

- [x] 1.1 Add `src/magicvibe/core/schemas/constants.py` with `DEFAULT_PAGE_SIZE = 10` and `MAX_PAGE_SIZE = 100`, and
  use them in `BaseFilterSchema.page_size` (`default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE`); verify with
  `uv run mypy src/magicvibe` (exit 0)
- [x] 1.2 Create `tests/__init__.py`, `tests/core/__init__.py` and `tests/core/test_schemas.py` covering the four
  scenarios of `specs/api-pagination/spec.md` at schema level, without a database: `page_size=100` accepted and
  echoed by `PaginatedResponse.build()`, `101` and `0` rejected with a validation error on `page_size`, omitted →
  10; verify `uv run pytest tests/core/` passes (exit 0, at least 4 tests)
- [x] 1.3 In `docs/architecture/testing.md` → Layout, add `tests/core/` for tests of shared `core` code (schemas,
  no database); verify the layout tree and its bullet list both mention it
- [x] 1.4 In `CLAUDE.md`, remove "`page_size` has no maximum of 100" from the "Known drift" list, and update the
  Gotchas item that says `tests/` does not exist yet (it now exists; `alembic/versions/` is still empty); verify
  neither statement remains

## 2. Integration checks

- [x] 2.1 Run `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests` and
  `uv run mypy src/magicvibe`; all exit 0 and pytest reports passed tests (not exit 5)
