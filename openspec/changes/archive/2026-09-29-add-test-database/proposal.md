# Proposal

## Why

[Testing](../../../docs/architecture/testing.md) says the API is tested against a real PostgreSQL in a disposable
container, with the schema created by Alembic. None of that exists: `alembic/versions/` is empty, so there is no
schema at all (not for tests and not for a deployment), `tests/conftest.py` only sets the service token, and the pytest
loop scope is per function. Every later change in the docs-alignment series needs database tests, so this comes second,
right after the error codes.

`alembic/env.py` also imports the application as `src.magicvibe`, which `testing.md` forbids (it loads the application
twice) and which fails in the Docker image, where only the installed `magicvibe` package exists.

## What Changes

- pytest configuration as in [Testing → Configuration](../../../docs/architecture/testing.md#configuration): one event
  loop per session; a `concurrency` marker.
- `tests/conftest.py`: `pytest_configure` starts one PostgreSQL container (the image from `docker-compose.yml`),
  points `DATABASE__*` and `AUTH__SERVICE_TOKEN` at it, and runs `sys.executable -m alembic upgrade head`; fixtures for
  the test engine (`NullPool`), a rolled-back transaction per test with `join_transaction_mode="create_savepoint"`,
  the unit of work, the app with `dependency_overrides`, an authenticated HTTP client, and real-commit sessions for
  `@pytest.mark.concurrency` tests with `TRUNCATE … RESTART IDENTITY CASCADE` afterwards.
- `tests/factories.py`: helpers that create users (with Telegram data), profiles, preferences, reactions, reports and
  bans.
- `alembic/env.py` imports `magicvibe` instead of `src.magicvibe` and drops a `user_module_prefix` that points to a
  module that does not exist.
- The first migration, generated with autogenerate from the current models against a throwaway container. It creates
  the schema as the models are **today**; the models are brought to
  [Data model](../../../docs/architecture/models.md) by the later changes, each with its own migration.
- First database tests, which also cover what `add-error-codes` could only test with constructed exceptions: unknown,
  deleted and banned acting users (`USER_NOT_FOUND`, `USER_BANNED`), the real constraint names read from asyncpg
  (`uq_reaction_pair`, `ix_bans_user_id`), and a concurrency test: two simultaneous bans of one user give exactly one
  201 and one 409 `BAN_ALREADY_ACTIVE`.

No API behavior changes, so this change has no spec delta (`skip_specs: true`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- Code: `pyproject.toml` (`[tool.pytest.ini_options]` only), `alembic/env.py`, `alembic/versions/` (first migration).
- Tests: `tests/conftest.py`, `tests/factories.py`, first `tests/<domain>/` database tests; `tests/test_exceptions.py`
  uses the shared `client` fixture.
- Running tests now needs Docker (as `testing.md` and `CLAUDE.md` already say). CI (`ubuntu-latest`) has Docker; the
  test workflow does not change.
- Docs: `CLAUDE.md` Gotchas and "Known drift" (migrations and test database now exist). `testing.md` already describes
  the setup and does not change unless the implementation shows a gap.
- No dependency changes: `pytest-asyncio`, `httpx` and `testcontainers` are already in the `test` group.
