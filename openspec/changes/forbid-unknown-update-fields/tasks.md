# Tasks

## 1. Base schema

- [ ] 1.1 Make `BaseUpdateSchema` in `src/magicvibe/core/schemas/base.py` derive from `BaseSchema`; verify
  `uv run mypy src/magicvibe` exits 0
- [ ] 1.2 `tests/core/test_schemas.py`: a subclass of `BaseUpdateSchema` rejects an unknown field with
  `extra_forbidden` and still rejects an empty body; verify `uv run --no-sync pytest tests/core` passes
- [ ] 1.3 API tests: `PATCH /reports/{id}` with `{"status": "resolved", "note": "x"}` and `PATCH /bans/{id}` with
  `{"expires_at": ...}` return 400 `VALIDATION_ERROR` / `extra_forbidden` and change nothing; verify
  `uv run --no-sync pytest tests/report tests/ban` passes

## 2. Integration checks

- [ ] 2.1 Run `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`,
  `uv run mypy src/magicvibe` and `npx openspec validate forbid-unknown-update-fields --strict`; all exit 0
