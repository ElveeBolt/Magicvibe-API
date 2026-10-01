# MagicVibe API

Backend for a Telegram dating bot: users & profiles, discovery (next candidate),
reactions & matches, reports, bans. The bot is the only client.

`<package>` below means `magicvibe`; the code lives in `src/<package>/`.

| Layer      | Tech                           |
|------------|--------------------------------|
| Language   | Python 3.14                    |
| Web        | FastAPI                        |
| ORM        | SQLAlchemy 2 (async, asyncpg)  |
| Database   | PostgreSQL 18                  |
| Migrations | Alembic                        |
| Validation | Pydantic v2, pydantic-settings |
| Logging    | structlog                      |

## Commands

uv only — never pip, poetry or venv activation.

| Purpose              | Command                                                 |
|----------------------|---------------------------------------------------------|
| Dev server (`:8000`) | `uv run uvicorn <package>.main:app --reload` — one only |
| Tests                | `uv run pytest`                                         |
| Lint                 | `uv run ruff check src tests`                           |
| Format check         | `uv run ruff format --check src tests`                  |
| Types                | `uv run mypy src/<package>`                             |
| Lockfile in sync     | `uv lock --check`                                       |
| New migration        | `uv run alembic revision --autogenerate -m "<message>"` |

Scope lint/types to `src` and `tests` as above: `mypy .` fails on duplicate module
paths, and `ruff .` reports errors in `.claude/` tooling that are not project code.

## Where the rules live

`docs/` is the source of truth (index: `docs/README.md`). Skills and `.claude/rules/`
describe procedure; the facts come from here:

| Topic                              | Document                           |
|------------------------------------|------------------------------------|
| Business rules, plans              | `docs/prd.md`, `docs/plans.md`     |
| Terms                              | `docs/glossary.md`                 |
| Tables, constraints, enums         | `docs/architecture/models.md`      |
| Code structure, layers, API style  | `docs/architecture/conventions.md` |
| Error codes and statuses           | `docs/architecture/errors.md`      |
| How to test                        | `docs/architecture/testing.md`     |

- If the code disagrees with the docs, change the code. If the rule itself must
  change, update the doc first. Never resolve a conflict silently.
- Known drift — the code must be brought to the docs: no `MAX_PROFILE_IMAGES`;
  no `data/regions/load.py` yet (the owner writes it); domain error codes are
  still in the `ErrorCode` enum in `core/exceptions.py`, not in
  `<domain>/exceptions.py`.

## How a request flows

- `main.py` mounts one `bot_router` (`router.py`) that requires a bearer service
  token on **every** route (`dependencies.require_service_token`).
- The acting user comes from the `X-Telegram-User-Id` header → `CurrentUserDep`
  (`user/dependencies.py`). The user must already exist via `POST /users`.
- router → `<Domain>ServiceDep` → service opens `async with self.uow:` →
  `self.uow.<repo>` → SQLAlchemy.
- Services raise exception classes: general ones from `core/exceptions.py`,
  domain ones from `<domain>/exceptions.py` (each subclasses a category class
  and sets its code); `exceptions.py` turns them into responses. Body, codes,
  statuses and owning domains: `docs/architecture/errors.md`.
- Shared bases: `core/schemas/base.py` (`BaseSchema`, `BaseFilterSchema`,
  `PaginatedResponse`), `core/database/alchemy/` (`Base` with BigInteger `id`,
  `TimestampMixin`, `AlchemyRepository`, UoW).

## Gotchas

- The test session applies every migration in `alembic/versions/` to its own
  container, so a model change without a migration breaks the database tests.
  `pytest` exiting 5 ("no tests ran") is not a pass.
- Settings are nested env vars with `__` (`DATABASE__HOST`, `AUTH__SERVICE_TOKEN`),
  loaded from `.env`, which you cannot read. `.env.example` shows the keys. If the
  DB is unreachable, ask — don't guess or edit env files.
- Tests start PostgreSQL in Docker (testcontainers). If Docker is not running,
  ask — never point the tests at another database.
- `discovery` has no models: `DiscoveryRepository` is a read-side query over
  `user` and `reaction` tables.

## Definition of done

- The checks above are green; new logic is covered under `tests/<domain>/` as
  described in `docs/architecture/testing.md`.
- Report evidence, not claims: the command run and its exit code / test count.
- Never delete or skip tests, and never weaken a ruff/mypy rule (config, `noqa`,
  `type: ignore`) to get green — fix the cause.
