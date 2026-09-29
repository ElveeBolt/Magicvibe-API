---
paths:
  - "src/*/*/**/*.py"
  - "tests/*/**/*.py"
---

# Domain structure rules

Invariants for domain modules under `src/<package>/<domain>/`, where `<package>` is the
project's top-level package (the single package directly under `src/`).
`src/<package>/core/` is shared infrastructure, not a domain, so these rules do not apply there.

The project's conventions document is the source of these rules (where it lives: `CLAUDE.md`). If this file and that
document differ, the document wins.

## Layout

```
src/<package>/<domain>/
├── __init__.py
├── router.py                  # HTTP layer
├── dependencies.py            # Depends(): auth, UoW / service injection
├── services.py                # business logic
├── repositories.py            # data access
├── constants.py               # hardcoded business constants
├── enums.py                   # enums shared by models and schemas
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

`__init__.py`, `router.py` and `services.py` always exist. Everything else exists only when the domain actually
has that concern — a domain with no persistence has no models/, repositories.py, and no migration.
Empty placeholder files are a violation, not a stub.

Extra files (utils.py, …) are allowed, but nothing that belongs in one of the files above may be moved into them.

## Layer responsibilities

- **`router.py`** — parse request → call service → return schema. No business
  rules, no queries. Receives a service or UoW via `Depends()`; never a `Session`
  and never a repository.
- **`services.py`** — all business logic. No FastAPI types (`Request`, `Response`,
  `HTTPException`, `Depends`) and no SQLAlchemy statements. Owns the UoW and uses
  it as an async context manager so the transaction boundary is one business
  operation. A CRUD service implements `AbstractService`.
- **`repositories.py`** — data access only, one repository per aggregate,
  subclassing `AlchemyRepository[Model, PkType]` with `model = <Model>`.
  Instantiated only inside the UoW. Repositories hold no business rules.
- **`constants.py`** — `UPPER_CASE` values hardcoded in the code that change
  business behaviour (`MAX_BIO_LENGTH`, `MAX_PROFILE_IMAGES`). Values that
  differ per environment belong in settings, and fixed sets of values belong in
  `enums.py`.
- **`enums.py`** — enums shared between models and schemas, so neither side owns
  the vocabulary.
- **`models/`** — SQLAlchemy models inheriting the shared `Base`. One aggregate
  per file, re-exported from `models/__init__.py` so Alembic and the UoW discover
  them. A model that is not re-exported is invisible to autogenerate.
- **`schemas/`** — Pydantic v2 only (`model_dump()`, `model_validate()`, `ConfigDict`).
- **`schemas/validators.py`** - plain functions that take one value and return it
  (possibly normalised) or raise `ValueError` / `PydanticCustomError`.
- **`schemas/types.py`**: `Annotated` type aliases in `PascalCase` that combine a base type with `Field(...)` /
  `StringConstraints(...)` / etc. and validators from `validators.py`

## Imports

- Relative imports inside `<package>`: `from ..core.database.alchemy.repository
  import AlchemyRepository`, `from .models import Reaction`.

## Behaviour

- Every endpoint and every I/O call (database, external services) is `async`.
- A change under `models/` requires a generated migration (see the conventional
  migrations rule).
- Every data rule is enforced as the project's conventions document says (in the schema and in the database, with
  the same constant); a rule that depends on other rows is checked in the service after locking those rows.
- Services report failures only with the shared exceptions from `core`, each carrying an error code from the project's
  errors document. A new code is added to that document first. Routers never build error responses themselves.
- New logic in a domain requires tests under `tests/<domain>/`:
  `test_router.py` for the HTTP contract, `test_services.py` for business rules,
  and `test_schemas.py` when `schemas/types.py` or `schemas/validators.py` exist,
  covering accepted and rejected inputs through `model_validate()`.
  Repositories are not tested directly; they are covered through services.