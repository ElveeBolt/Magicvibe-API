# Tasks

## 1. Docs first

- [x] 1.1 `docs/prd.md` 6.6: a user without discovery preferences is not shown to others (the fit in their direction
  cannot be checked); `docs/glossary.md` Candidate: "…has preferences…"; verify both say so

## 2. Discovery

- [x] 2.1 `UserPublicSchema` gets `last_seen_at`; `DiscoveryService` raises `PROFILE_REQUIRED` / `PREFERENCES_REQUIRED`
  and passes city and goal both ways; `DiscoveryRepository` joins preferences and filters all four criteria in both
  directions, random order only; the route returns `UserPublicSchema | None`; delete `discovery/schemas/`; verify mypy
  and ruff
- [x] 2.2 Tests: `tests/discovery/test_router.py` for every `discovery` scenario (who may browse, each exclusion, each
  criterion in each direction, `null` any, age boundaries, reported user, public profile without Telegram data,
  `null` body, random order); `tests/discovery/test_services.py` for `PROFILE_REQUIRED` / `PREFERENCES_REQUIRED`;
  verify `uv run --no-sync pytest tests/discovery` passes

## 3. Integration checks

- [x] 3.1 Run `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`,
  `uv run mypy src/magicvibe` and `npx openspec validate align-discovery --strict`; all exit 0
