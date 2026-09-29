# Tasks

## 1. Alembic and the first migration

- [ ] 1.1 In `alembic/env.py` import `magicvibe.…` instead of `src.magicvibe.…` and remove the `user_module_prefix`
  arguments; verify `grep -n "src\." alembic/env.py` finds nothing
- [ ] 1.2 Start a throwaway `postgres:18.6` container, run `uv run alembic revision --autogenerate -m "create initial
  schema"` with `DATABASE__*` pointing at it, remove the container; verify one file appears in `alembic/versions/`
  that creates `users`, `user_telegrams`, `user_profiles`, `user_preferences`, `reactions`, `reports`, `bans` and their
  enum types, and `docker ps -a` shows no leftover container

## 2. pytest configuration and fixtures

- [ ] 2.1 In `pyproject.toml` set `asyncio_default_fixture_loop_scope` and `asyncio_default_test_loop_scope` to
  `"session"` and register the `concurrency` marker; verify `uv run pytest --markers | grep concurrency`
- [ ] 2.2 Extend `tests/conftest.py`: container start, `DATABASE__*` variables and `alembic upgrade head` in
  `pytest_configure`, container stop in `pytest_unconfigure`; fixtures `engine`, `connection`, `session_factory`,
  `session`, `uow`, `app`, `client`, and `concurrent_app` / `concurrent_client` with truncation; verify
  `uv run pytest` starts the container, creates the schema and the existing 31 tests still pass
- [ ] 2.3 Make `tests/test_exceptions.py` use the shared `client` fixture instead of its own; verify its tests pass
- [ ] 2.4 Add `tests/factories.py` with `create_user`, `create_profile`, `create_preference`, `create_reaction`,
  `create_report`, `create_ban`; verify through the tests of group 3

## 3. First database tests

- [ ] 3.1 `tests/user/test_router.py`: a request with an unknown `X-Telegram-User-Id` returns 404 `USER_NOT_FOUND`, a
  soft-deleted user returns 404 `USER_NOT_FOUND`, a banned user returns 403 `USER_BANNED` with exactly
  `ban: {reason, comment}`; verify `uv run pytest tests/user` passes
- [ ] 3.2 `tests/core/test_constraints.py` (or the domain folders): inserting a second reaction for the same pair and a
  second active ban through the session raises `IntegrityError` whose name, read by
  `magicvibe.exceptions.constraint_name`, is `uq_reaction_pair` / `ix_bans_user_id`; verify the tests pass
- [ ] 3.3 `tests/ban/test_router.py`: a `@pytest.mark.concurrency` test sends two `POST /bans` for one user at once
  with `asyncio.gather`; exactly one returns 201 and the other 409 `BAN_ALREADY_ACTIVE`, and the next test starts with
  empty tables; verify `uv run pytest tests/ban` passes twice in a row
- [ ] 3.4 Rollback isolation: a test that creates a user and a following test that counts users see independent
  data; verify with `uv run pytest tests/core/test_isolation.py`

## 4. Docs

- [ ] 4.1 In `CLAUDE.md` update the Gotchas (migrations exist; database tests run in Docker) and remove "the pytest
  config and testcontainers are not set up yet" from "Known drift"; verify neither outdated statement remains
- [ ] 4.2 Compare the finished setup with `docs/architecture/testing.md`; if anything differs (fixture names, image,
  marker), update the document; verify the Layout and Isolation sections match `tests/conftest.py`

## 5. Integration checks

- [ ] 5.1 Run `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`,
  `uv run mypy src/magicvibe` and `npx openspec validate add-test-database --strict`; all exit 0, pytest reports
  passed tests, and `docker ps` shows no test container after the run
