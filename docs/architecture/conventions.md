# Conventions

Rules for code in this repository. They apply to every domain.

## Repository layout

Only the folders whose purpose is not obvious from the name:

| Folder  | Holds                                                                                |
|---------|--------------------------------------------------------------------------------------|
| `data/` | Reference data and the scripts that load it (see [Regions data](./region_data.md))   |
| `docs/` | Product and architecture documentation                                               |

## Package structure

```
src/<package>/
├── main.py              # creates the FastAPI app: logging, middleware, bot_router, exception handlers
├── router.py            # bot_router: includes every domain router, requires the service token
├── dependencies.py      # shared Depends(): require_service_token, get_uow
├── exceptions.py        # maps core exceptions to HTTP responses (register_exception_handlers)
├── settings.py          # pydantic-settings; nested env vars with `__`
├── uow.py               # UnitOfWork with the repository of every domain
├── logging_config.py    # structlog setup
├── metadata.py          # app title, version and description from package metadata
├── middlewares/         # HTTP middleware (logging_middleware.py)
├── core/                # shared infrastructure, no business logic
│   ├── generics/        # abstract base classes: repository, service, unit of work
│   ├── database/
│   │   └── alchemy/     # SQLAlchemy implementations: Base, mixins, enum_type, repository, service, UoW, setup
│   ├── schemas/         # BaseSchema, BaseFilterSchema, PaginatedResponse, shared validators
│   └── exceptions.py    # ServiceError, category classes (NotFoundError, ConflictError, …), general codes
└── <domain>/            # see Domain structure
```

- A new domain is registered in two places: its router in `router.py` and its repository in `uow.py`.
- `core/` holds no business logic and never imports from domains.
- The app version is never hard-coded; `metadata.py` reads it from package metadata (see
  [Versioning](../process/versioning.md)).

## Domain structure

```
src/<package>/<domain>/
├── __init__.py
├── router.py                  # HTTP layer
├── dependencies.py            # Depends(): auth, UoW / service injection
├── services.py                # business logic
├── repositories.py            # data access
├── constants.py               # business constants
├── enums.py                   # enums shared by models and schemas
├── exceptions.py              # exceptions for the codes this domain owns (see Errors)
├── models/
│   ├── __init__.py
│   ├── <entity>.py            # one SQLAlchemy aggregate per file
│   └── <entity>_<sub>.py      # nested entity of the same aggregate
└── schemas/
    ├── __init__.py
    ├── types.py               # reusable Annotated field types
    ├── validators.py          # pure field-level validation functions
    ├── <entity>.py            # Pydantic v2 schemas for the entity
    └── <entity>_<sub>.py
```

Domain folder names are singular (`user`, `region`, `reaction`, `subscription`, `report`, `ban`). A read-side domain
without its own tables (for example `discovery`) has no `models/` folder.

Shared infrastructure lives in `core` (for example `core.database.alchemy` with `Base`, mixins and `enum_type`). Reuse
it instead of writing new helpers.

## Layers

| Layer             | Does                                            | Never does           |
|-------------------|-------------------------------------------------|----------------------|
| `router.py`       | Parses input, calls a service, returns a schema | SQL, business rules  |
| `dependencies.py` | Provides `Depends()`: auth, UoW, services       | SQL, business rules  |
| `services.py`     | Business rules, transactions via Unit of Work   | Build HTTP responses |
| `repositories.py` | Database access                                 | Business decisions   |

- Business numbers (limits, lengths, ages) live in `constants.py`, never inline.
- Full type hints everywhere; code must pass ruff and mypy.

## Models

- `Mapped[...]` with `mapped_column`.
- Enums via `enum_type(...)`.
- Indexes as `Index(None, ...)`, relying on the naming convention.
- Every `CheckConstraint` has a name.
- Every data rule is enforced twice, with the same constant from `constants.py`: in the Pydantic schema (so the bot gets
  a clear 400) and in the database (`varchar(N)`, named `CHECK`, unique, foreign key). Two exceptions:
    - a rule that depends on the current time (age): schema only;
    - a rule that depends on other rows (photo limit, one current subscription, a match for mutual likes): checked in
      the service, in the same transaction, after locking the parent rows with `SELECT … FOR UPDATE` (several rows in
      ascending `id` order), so concurrent requests cannot both pass or both miss the check.
- Database defaults via `server_default`.
- Timestamps from `TimestampMixin` (`created_at`, `updated_at`) or `CreatedAtMixin` (`created_at`).
- Tables, columns, foreign keys and constraints follow the [Data model](./models.md).

## Schemas

- Pydantic v2.
- Naming: `*CreateSchema`, `*UpdateSchema` (all fields optional, for PATCH), `*ReadSchema`.
- Reusable constrained types (`Name`, `Bio`, `Message`, …) live in `schemas/types.py` as `Annotated` types.
- Schemas forbid unknown fields: `extra="forbid"`, inherited from `BaseSchema`.

## API style

- No version in URL paths; paths start with the resource (`/users/{user_id}`).
- JSON in and out, except photo upload (`multipart/form-data`).
- Page-based pagination and the business error shape below are part of the API contract.

### Errors

- `core/exceptions.py` holds the mechanism: `ServiceError`, one category class per status (`BadRequestError`,
  `ForbiddenError`, `NotFoundError`, `ConflictError`, …) and the general codes. It knows nothing about the domains.
- A code owned by a domain is an exception class in `<domain>/exceptions.py` that subclasses a category class and sets
  the code, for example `class AlreadyReactedError(ConflictError)` with `ALREADY_REACTED`. Other domains import it
  from the owning domain.
- Services raise exception classes, never a category class with a domain code passed in. `exceptions.py` turns them
  into responses. Routers never build error responses themselves.
- The response body, the list of codes and their statuses: [Errors](./errors.md).

### Pagination

List endpoints take query parameters `page` (from 1, default 1), `page_size` (from 1 to 100, default 10), `order_by` and
`order` (`asc` or `desc`, default `desc`). They return:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "pages": 1,
  "page_size": 10
}
```

`pages` is at least 1, even when there are no items.

A `page_size` above 100 is rejected with `VALIDATION_ERROR` ([Errors](./errors.md#validation-errors)).

## Migrations

- Every model change comes with an Alembic migration.
- A migration file may be generated with `uv run alembic revision --autogenerate`. Applying migrations
  (`alembic upgrade` / `alembic downgrade`) is done **only by a person, manually**. The only exception: tests apply
  migrations to their own throwaway container (see [Testing → Schema](./testing.md#schema)).
- PostgreSQL enum changes (new types, added or removed values) are generated by autogenerate too: `alembic/env.py`
  loads `alembic-postgresql-enum`.
- Autogenerate does not detect a check constraint added to an existing table. Such a constraint is appended by hand to
  the newly generated, not yet merged migration: only `op.create_check_constraint` in `upgrade` and `op.drop_constraint`
  in `downgrade`, with the model's name and expression. A test expects the constraint by name.
- Migrations change the schema only. They never load data and never call scripts.
- Migrations never import ORM models or services.
- A merged migration is never edited; fix mistakes with a new migration.

## Tests

- Every change to logic comes with tests. How to test: [Testing](./testing.md).

## Dependencies

- Use `uv` package manager only (never pip or poetry).
- Dependencies must be categorized into specific groups in pyproject.toml (e.g., `lint`, `test`). The dev group must
  include the lint and test groups.

## Configuration and secrets

- All settings come from environment variables via pydantic-settings.
- `.env.example` is committed and lists every setting.
- No secrets in code or logs.

## Language

Code, comments, docstrings, commit messages and documentation are in English.