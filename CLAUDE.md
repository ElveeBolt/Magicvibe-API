# MagicVibe API

Backend for a Telegram dating bot: users & profiles, discovery (next candidate),
reactions & matches, reports, bans. The bot is the only client.

`<package>` below means `magicvibe`; the code lives in `src/<package>/`.

Product and architecture docs live in `docs/`; start with `docs/README.md`.

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

## How a request flows

- `main.py` mounts one `bot_router` (`router.py`) that requires a bearer service
  token on **every** route (`dependencies.require_service_token`).
- The acting user comes from the `X-Telegram-User-Id` header → `CurrentUserDep`
  (`user/dependencies.py`). The user must already exist via `POST /users`.
- router → `<Domain>ServiceDep` → service opens `async with self.uow:` →
  `self.uow.<repo>` → SQLAlchemy.
- Services signal failures with `core/exceptions.py` (`NotFoundError`,
  `ConflictError`, `BadRequestError`, `ForbiddenError`, `GoneError`); `exceptions.py`
  maps them to 404/409/400/403/410. DB `IntegrityError` → 409.
- Shared bases: `core/schemas/base.py` (`BaseSchema`, `BaseFilterSchema`,
  `PaginatedResponse`), `core/database/alchemy/` (`Base` with BigInteger `id`,
  `TimestampMixin`, `AlchemyRepository`, UoW).

## Gotchas

- `tests/` does not exist yet and `alembic/versions/` is empty. `pytest` currently
  exits 5 ("no tests ran") — that is not a pass. Drop `tests` from the lint paths
  until the directory exists.
- Settings are nested env vars with `__` (`DATABASE__HOST`, `AUTH__SERVICE_TOKEN`),
  loaded from `.env`, which you cannot read. `.env.example` shows the keys. If the
  DB is unreachable, ask — don't guess or edit env files.
- `discovery` has no models: `DiscoveryRepository` is a read-side query over
  `user` and `reaction` tables.

## Definition of done

- The checks above are green; new logic is covered under `tests/<domain>/`.
- Report evidence, not claims: the command run and its exit code / test count.
- Never delete or skip tests, and never weaken a ruff/mypy rule (config, `noqa`,
  `type: ignore`) to get green — fix the cause.
