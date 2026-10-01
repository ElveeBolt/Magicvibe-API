# Testing

How the MagicVibe API is tested. Every business rule in the [PRD](../prd.md) and [Plans](../plans.md), and every
constraint in the [Data model](./models.md), is covered by at least one automated test.

## Stack

| Tool             | Purpose                                                                        |
|------------------|--------------------------------------------------------------------------------|
| `pytest`         | Test runner                                                                    |
| `pytest-asyncio` | Async tests; `asyncio_mode = "auto"`, so `async def` tests need no marker      |
| `httpx`          | `AsyncClient` with `ASGITransport` calls the FastAPI app in-process, no server |
| `testcontainers` | Starts a disposable PostgreSQL container for the test session                  |
| `alembic`        | Creates the schema in the test database                                        |

Test dependencies go into the `test` group, added with `uv add --group test <package>` (never by editing
`pyproject.toml` by hand).

## Configuration

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
asyncio_default_test_loop_scope = "session"
```

- **One event loop per session.** The database engine is created once per test session, and an asyncpg connection
  works only in the loop that opened it, so fixtures and tests share one loop.
- **`__init__.py` in every test folder**, including `tests/` itself. Every domain folder has files with the same names
  (`test_router.py`, `test_services.py`); as packages they get distinct module names (`tests.user.test_router`,
  `tests.reaction.test_router`), so pytest's default import mode works without "import file mismatch" errors. A folder
  without `__init__.py` brings that error back.
- **Imports in tests.** Helpers are imported by their package path (`from tests.factories import …`). The application
  is imported only as `magicvibe`, never as `src.magicvibe`: the repository root is on `sys.path` during tests, and
  importing both names would load the application twice.

## Database

Tests run against a real **PostgreSQL** in a Docker container that
[testcontainers](https://testcontainers-python.readthedocs.io/) starts for each test session.

### Requirements

- Docker must be running. Nothing else is set up by hand: no test database, no extra settings in `.env`.
- If Docker is not available, the test session fails at start. Start Docker; never point the tests at another
  database instead.

### The container

- One container per test session, started before the first test and removed after the last one. Every run starts from
  an empty database.
- The image is the same as in `docker-compose.yml`. When the PostgreSQL version changes, it changes in
  both places.
- The development database is never touched by tests: it is not even reachable from the test configuration.

### Settings

The application reads its settings from environment variables, which take priority over `.env`. The test setup uses
this:

1. The container is started in the `pytest_configure` hook, before any test module is imported.
2. The hook sets `DATABASE__HOST`, `DATABASE__PORT`, `DATABASE__USERNAME`, `DATABASE__PASSWORD` and `DATABASE__NAME`
   to the container's values, and `AUTH__SERVICE_TOKEN` to a fixed test token.
3. Only after that is the application imported, so its settings, its engine and Alembic all point to the container.

For this to work, `tests/conftest.py` never imports the application (`magicvibe`) at module level; it imports it
inside fixtures.

### Schema

- The schema is created once per session by running `alembic upgrade head` as a separate process with the same
  Python interpreter (`sys.executable -m alembic upgrade head`) and the environment variables above. A separate
  process keeps Alembic's own event loop away from the test loop. `uv run` is not used here: it would sync the
  environment again, which in CI adds groups the test run does not install.
- Until the first migration exists, the schema is empty and every database test fails. The first migration comes
  before the first test.
- Applying migrations in tests is the one exception to the rule that migrations are applied only by a person
  ([Conventions → Migrations](./conventions.md#migrations)). It is allowed only because the database is a throwaway
  container.

### Isolation

- The application's own engine and `async_session_factory` are not used in tests. The test setup creates its own
  engine (with `NullPool`) and passes its session factory to the unit of work through `app.dependency_overrides`.
- Each test runs inside a transaction that is rolled back at the end. The session is bound to that transaction with
  `join_transaction_mode="create_savepoint"`, so a `commit()` made by the unit of work only releases a savepoint and
  nothing reaches the database. Tests do not see each other's data and need no cleanup.
- Concurrency tests (see below) need real commits, so they do not use the rolled-back transaction. They are marked
  `@pytest.mark.concurrency`; a fixture gives them their own sessions and, after the test, empties every table with
  `TRUNCATE … RESTART IDENTITY CASCADE`, so the next test again starts from an empty database.
- Tests run one at a time (no `pytest-xdist`): all of them share one database.

### CI

The GitHub Actions runner (`ubuntu-latest`) has Docker, so CI runs the tests exactly as locally: no database service
and no database settings in the workflow.

## Layout

```
tests/
├── __init__.py
├── conftest.py            # engine, rolled-back transaction, app, HTTP client and auth fixtures
├── factories.py           # helpers that create users, profiles, reactions, bans … in the database
├── core/                  # shared code from src/<package>/core/
│   ├── __init__.py
│   ├── test_exceptions.py # every exception class's code and status match errors.md, codes are unique; no database
│   └── test_schemas.py    # shared schemas (filters, pagination), no database
├── test_exceptions.py     # app-level error handlers: error body, validation, framework and unexpected errors
└── <domain>/              # same names as src/<package>/<domain>/
    ├── __init__.py
    ├── conftest.py        # fixtures used only by this domain (its services, ready-made objects)
    ├── test_router.py     # HTTP contract
    ├── test_services.py   # business rules
    ├── test_models.py     # database constraints, one test per named constraint
    └── test_schemas.py    # accepted and rejected inputs, when schemas/types.py or validators.py exist
```

- One folder per domain, with the same name as the domain package (`user`, `reaction`, `report`, …).
- A rule with many time-dependent cases may get its own file next to them, named after the rule (for example
  `tests/reaction/test_limits.py` for the daily limits).
- Shared code from `core` is tested in `tests/core/`. Tests there that need no database (schemas, pure functions) use
  no database fixtures.
- App-level code outside `core` and the domains (the exception handlers in `exceptions.py`) is tested in
  `tests/test_exceptions.py`, through the real app for errors raised before any database access and through a small
  app with the same handlers for the rest.
- Fixtures needed by every domain live in `tests/conftest.py`; a domain `conftest.py` holds only what that domain
  needs. pytest makes fixtures from both files available to the tests in the domain folder.
- Fixtures that replace a FastAPI dependency do it through `app.dependency_overrides`; the `app` fixture clears the
  overrides after each test.
- Repositories are not tested directly; they are covered through services.
- Test data is created through factories, not through copied SQL or long inline setup.

## What to test

### Service tests

`test_services.py` checks the business rules by calling the service directly, with a unit of work bound to the test
transaction. Most rule cases live here: every state that changes the outcome (banned, hidden, no profile, no
preferences, daily limit reached, …) and every rejection, with the expected exception.

### API tests

`test_router.py` checks the HTTP contract. Tests call the API through `httpx.AsyncClient` with the service token and
`X-Telegram-User-Id`, exactly as the bot does, against the real test database. Services are not mocked.

Each endpoint has tests for:

- the successful case: status code, response body and, when needed, the database state;
- each error the endpoint can return: the status, the `code` and its extra fields from [Errors](./errors.md), never
  the `detail` text. The rule behind the error is covered in the service tests; the API test checks only the mapping;
- a missing or wrong service token (`INVALID_SERVICE_TOKEN`), an unknown acting user (`USER_NOT_FOUND`) and a banned
  acting user (`USER_BANNED`);
- privacy ([NFR-04](./nfr.md)): Telegram data and like messages never appear outside match data.

### Data rules

Every rule is enforced twice ([NFR-03](./nfr.md)), and both sides are tested:

- the schema rejects the value with 400 `VALIDATION_ERROR`;
- the database rejects the same value when it bypasses the schema (insert through the session, expect
  `IntegrityError`). One test per named constraint in the [Data model](./models.md), in the domain's
  `test_models.py`; it also checks the constraint name the API maps to an error code.

### Rules that depend on other rows

Rules checked in the service after `SELECT … FOR UPDATE` (photo limit, one current subscription, a match for mutual
likes) have a **concurrency test**: two requests run at the same time with `asyncio.gather`, and exactly one outcome
is allowed (for example, two opposite likes create exactly one match).

### Time

Rules that depend on time (age, daily limit reset at midnight Europe/Kyiv, subscription expiry) are tested at their
boundaries: just before and just after midnight Kyiv time, on the day of the 18th birthday, at `expires_at`. Tests
never wait for real time to pass and never depend on the current date.

## What is not tested here

- The Telegram bot (separate repository).
- Performance targets.
- External services: S3 is replaced with a fake in tests. The API never calls Telegram.

## Rules

- New logic comes with tests in the same change.
- A bug fix comes with a test that fails without the fix.
- Our own services, repositories and the database are never mocked. Fakes replace only external services.
- Tests are never deleted, skipped or marked `xfail` to get a green run; fix the cause.
- `pytest` exiting with code 5 ("no tests ran") is not a pass.