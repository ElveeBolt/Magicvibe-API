# Design

## Context

- `testing.md` fixes most of the setup (container per session, settings via environment, Alembic in a subprocess,
  rolled-back transaction with savepoints, `dependency_overrides`, concurrency tests with real commits). This design
  records only the choices it leaves open.
- `tests/conftest.py` (from `add-error-codes`) already sets `AUTH__SERVICE_TOKEN` in `pytest_configure` and never
  imports `magicvibe` at module level.
- Every router gets its unit of work from `magicvibe.dependencies.get_uow` (`UOWDep`), and every service opens
  `async with self.uow:`, which commits or rolls back on exit.
- `testcontainers` 4.15 ships `testcontainers.community.postgres.PostgresContainer` (the old
  `testcontainers.postgres` path is deprecated); it waits for readiness with `psql` inside the container, so no
  database driver is needed on the host side.

## Goals / Non-Goals

**Goals:**

- `uv run pytest` works on a machine with Docker and nothing else, locally and in CI.
- Tests are isolated without cleanup code; concurrency tests can commit for real.

**Non-Goals:**

- Bringing models to `models.md` (later changes, each with its own migration).
- One test per named constraint: each later change adds the constraint tests for the tables it aligns, because the
  constraints themselves change there.

## Decisions

### Container and schema in `pytest_configure`

The container is started in `pytest_configure` (image `postgres:18.6`, the one in `docker-compose.yml`), the
`DATABASE__*` variables are set from `get_container_host_ip()` / `get_exposed_port(5432)`, and
`subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)` creates the schema before any test
module is imported. `pytest_unconfigure` stops the container. If Docker is not running, `PostgresContainer.start()`
raises and the session fails at start, as `testing.md` requires.

*Alternative:* a session fixture. Rejected: `testing.md` needs the variables set before the application is imported,
and test modules (`tests/test_exceptions.py`, `tests/core/`) import `magicvibe` at collection time.

### Isolation

- `engine` (session scope): `create_async_engine(url, poolclass=NullPool)` built from `magicvibe.settings`.
- `connection` (per test): `await engine.connect()`, `begin()` an outer transaction, roll it back after the test.
- `session_factory` (per test): `async_sessionmaker(bind=connection, join_transaction_mode="create_savepoint",
  expire_on_commit=False)`. Each unit of work opens its own session from it; its `commit()` only releases a savepoint.
- `uow`: `UnitOfWork(session_factory)` for service tests; `session`: one session from the same factory for factories
  and for direct constraint tests.
- `app`: `magicvibe.main.app` with `dependency_overrides[get_uow] = lambda: UnitOfWork(session_factory)`, cleared
  after the test. `client`: `httpx.AsyncClient(ASGITransport(app))` with the bearer token; tests add
  `X-Telegram-User-Id` themselves.
- Concurrency tests (`@pytest.mark.concurrency`): a `concurrent_app` fixture overrides `get_uow` with the real-commit
  `async_sessionmaker(engine)`; afterwards every table in `Base.metadata.sorted_tables` is emptied with one
  `TRUNCATE … RESTART IDENTITY CASCADE`.

### Factories are plain async functions

`tests/factories.py` has `create_user(session, *, telegram_id=None, status=…)`, `create_profile`,
`create_preference`, `create_reaction`, `create_report`, `create_ban`, each adding ORM objects and flushing, with
unique defaults from a counter. *Alternative:* factory-boy — rejected, it would be a new dependency and its async
support is thin.

### The first migration is generated, not written

Per the migrations rule, `uv run alembic revision --autogenerate -m "create initial schema"` is run against a
throwaway `postgres:18.6` container (`docker run --rm -d -p <free port>:5432`), with `DATABASE__*` pointing at it and
the container removed afterwards; the development database and `.env` are not touched. The file is then applied by
the test session itself, which proves it creates a working schema.

### `alembic/env.py`

Imports switch from `src.magicvibe.…` to `magicvibe.…`, the model imports stay explicit (they register the tables in
`Base.metadata`), and the `user_module_prefix` pointing to `src.core.database.alchemy.migration_types` (no such
module) is removed, so a custom type would be rendered with its real import path.

## Risks / Trade-offs

- [Sharing one enum type between two tables (`user_profile_gender_enum` on profiles and preferences) can make the
  migration create the type twice] → the test session's `alembic upgrade head` catches it; if it happens, the model
  passes `metadata=Base.metadata` to `enum_type` (as its docstring says) before the migration is generated.
- [Container start adds a few seconds to every run, also for tests that need no database] → accepted; `testing.md`
  asks for one container per session.
- [The first migration encodes models that are known to differ from `models.md`] → intended: later changes migrate
  from it; nothing has been deployed with a schema yet, so there is nothing to migrate in production besides this.
