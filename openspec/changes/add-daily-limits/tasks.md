# Tasks

## 1. Daily limits

- [ ] 1.1 `reaction/constants.py` `LIMIT_TIME_ZONE`; `ReactionRepository.day_bounds`, `count_since`,
  `exists_pair`; `ReactionService.create` in the order of the design (repeat, plan, superlike, limit), raising
  `PREMIUM_REQUIRED` and `DAILY_LIMIT_REACHED` with `limit_type`, `resets_at` and `Retry-After`; verify mypy and ruff
- [ ] 1.2 Tests in `tests/reaction/`: every "Daily limits" scenario through the API (with made-up `created_at` just
  before and at `day_start`), a `@pytest.mark.concurrency` test of parallel likes at the limit, and `day_bounds` at
  23:59:59.999999 / 00:00 Kyiv and on the spring and autumn DST dates (23 and 25 hour days); update existing reaction
  tests that superlike on the free plan; verify `uv run --no-sync pytest tests/reaction` passes

## 2. Who liked me

- [ ] 2.1 `ReactionRepository.get_likers` / `count_likers`, `LikerReadSchema`, `ReactionService.get_likers` with the
  plan check, route `GET /likers`; verify `app.openapi()` lists it
- [ ] 2.2 Tests for every `likers` scenario; verify `uv run --no-sync pytest` passes

## 3. Integration checks

- [ ] 3.1 Run `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`,
  `uv run mypy src/magicvibe` and `npx openspec validate add-daily-limits --strict`; all exit 0
