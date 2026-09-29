# Tasks

## 1. Models and migration

- [x] 1.1 `reaction/models/match.py` (`Match`) and the reaction model changes (`message_not_empty`, composite index,
  no `from_user_id` index); register `Match` in `alembic/env.py`; verify mypy
- [x] 1.2 Generate the migration on a throwaway `postgres:18.6` container and append only the `message_not_empty`
  check (upgrade and downgrade); verify the file creates `matches` with its constraints and index, swaps the reaction
  indexes, has the check, and the test session applies it

## 2. Reactions and matches

- [x] 2.1 `UserRepository.lock_many`; `MatchRepository` (`create`, `get_for_user`, `count_for_user`) in `uow.match`;
  `ReactionRepository.get_like(from, to)`; remove the derived-match queries
- [x] 2.2 Schemas `MatchContactSchema`, `MatchReadSchema`; `ReactionService.create` (lock, banned target 404, match
  in the same transaction) and `get_matches` (from `matches`, banned partners hidden); verify mypy and ruff
- [x] 2.3 `tests/factories.py`: `create_match`; `tests/reaction/test_router.py` for every `reactions` and `matches`
  scenario, with a `@pytest.mark.concurrency` test of opposite likes at the same time; `tests/reaction/test_models.py`
  for `message_not_empty`, `super_only_on_like`, `message_only_on_like`, `not_self`, `ordered_pair`,
  `uq_match_pair`; `tests/reaction/test_services.py` for the match rule; verify `uv run --no-sync pytest` passes

## 3. Integration checks

- [x] 3.1 Run `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`,
  `uv run mypy src/magicvibe` and `npx openspec validate add-matches --strict`; all exit 0
