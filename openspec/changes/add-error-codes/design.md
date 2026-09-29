# Design

## Context

- `core/exceptions.py` has `NotFoundError`, `ConflictError`, `BadRequestError`, `ForbiddenError` (with `details`)
  and `GoneError`, none with a code. `exceptions.py` registers one handler per class, each returning
  `{"detail": str(exc)}`, plus an `IntegrityError` handler that returns a bare 409.
- `require_service_token` raises FastAPI's `HTTPException(401)`; FastAPI's own handlers produce 422 for
  `RequestValidationError` and `{"detail": "Not Found"}` for unknown paths.
- `LoggingMiddleware` binds `request_id` into structlog contextvars only; nothing else can read it.
- There is no test database yet (`add-test-database` comes next), so this change is tested without one.

## Goals / Non-Goals

**Goals:**

- One place that knows the status of each code, so a service cannot raise a code with the wrong status.
- Services keep raising the same exception classes; only the code (and extra fields) are added at raise sites.

**Non-Goals:**

- Raising codes for rules that are not built yet (see proposal).
- Removing the soft delete itself (`hard-delete-accounts`).
- Tests that need a database: constraint mapping is tested with constructed exceptions; the real
  constraint-violation tests come with the database tests of each domain.

## Decisions

### `ErrorCode` and statuses live in `core/exceptions.py`

`ErrorCode(StrEnum)` lists every code from `errors.md`; `ERROR_STATUSES: dict[ErrorCode, int]` gives each its status.
`ServiceError.__init__(detail, code, extra=None, headers=None)` stores them and exposes `status_code` from the table.
The existing classes stay as convenient defaults (`NotFoundError` → `NOT_FOUND`, `ConflictError` → `CONFLICT`,
`BadRequestError` → `BAD_REQUEST`, `ForbiddenError` → no default, it always names its code), and
`UnauthorizedError` is added for the token check. `GoneError` is removed.

*Alternative:* status per class, code chosen freely. Rejected: `ConflictError(code=USER_BANNED)` would silently send
409 instead of 403. With the table, the status follows the code, and a test checks the table against `errors.md`.

### One handler per error source in `exceptions.py`

- `ServiceError` → `{"code", "detail", **extra}` with `exc.status_code` and `exc.headers`.
- `RequestValidationError` → 400 `VALIDATION_ERROR`; each Pydantic error becomes `{field, type, message}`. `field`
  is `loc` without its first element when that is a request part (`body`, `query`, `path`, `header`, `cookie`),
  joined with `.`; integer indexes are kept as path segments.
- `StarletteHTTPException` (raised by routing) → 404 `NOT_FOUND`, 405 `METHOD_NOT_ALLOWED`; any other status maps to
  `BAD_REQUEST` (4xx) or `INTERNAL_ERROR` (5xx), keeping the original status.
- `IntegrityError` → code by constraint name. The name is read from the asyncpg exception that SQLAlchemy wraps
  (`exc.orig.__cause__.constraint_name`, falling back to `exc.orig.constraint_name`). The mapping
  `{"uq_reaction_pair": ALREADY_REACTED, "ix_bans_user_id": BAN_ALREADY_ACTIVE}` is in `exceptions.py` (the app
  level may know domain constraint names; `core` may not). `ix_bans_user_id` is the name the naming convention gives
  the partial unique index on `bans.user_id`. The raw message is logged with `logger.warning`.
- `Exception` → 500 `INTERNAL_ERROR` with `request_id`, logged with `logger.exception`.

### Request ID reaches the 500 handler through `scope["state"]`

Starlette calls the `Exception` handler from `ServerErrorMiddleware`, outside `LoggingMiddleware`. The middleware
already computes the request ID; it also stores it in `scope["state"]["request_id"]`, which the handler reads as
`request.state.request_id`. *Alternative:* read structlog contextvars in the handler — rejected, it depends on how
the ASGI stack propagates context.

### Service token raises a service exception

`require_service_token` raises `UnauthorizedError(INVALID_SERVICE_TOKEN, headers={"WWW-Authenticate": "Bearer"})`,
so it goes through the same handler. It is a router dependency and runs before the endpoint's parameters are
validated, so a bad token wins over a bad body.

### Raise sites

| Where                                 | Today                         | After                                          |
|---------------------------------------|-------------------------------|------------------------------------------------|
| `UserService.get_acting_user`         | 404 / 410 / 403 full ban      | `USER_NOT_FOUND` (unknown or deleted) / `USER_BANNED` with `ban: {reason, comment}` |
| `UserService.soft_delete`, banned     | 403 no code                   | `USER_BANNED` with `ban`                       |
| `UserService.soft_delete` / `restore` | 409                           | `CONFLICT` (temporary until `hard-delete-accounts`) |
| `UserService.update_preference`       | 400 `BadRequestError`         | 400 `VALIDATION_ERROR`, `errors: [{field: "", type: "value_error", message}]` — same as the schema's own range check on `PUT` |
| `ReactionService.create`              | 400 / 404 / 409               | `SELF_ACTION` / `NOT_FOUND` / `ALREADY_REACTED` |
| `ReportService.create_by_reporter_id` | 400 / 404                     | `SELF_ACTION` / `NOT_FOUND`                    |
| `BanService.create`                   | 404 / 409                     | `NOT_FOUND` / `BAN_ALREADY_ACTIVE`             |
| `BanService.lift`                     | 409                           | `CONFLICT`                                     |
| `DiscoveryService.get_next_candidate` | 400                           | 409 `PROFILE_REQUIRED`                         |
| Other `NotFoundError`s                | 404                           | `NOT_FOUND`                                    |

`get_acting_user` also stops setting `status = active` when it finds no active ban: only the `ban` domain changes
`users.status` ([Data model → `users`](../../../docs/architecture/models.md#users)).

### Tests without a database

`tests/conftest.py` sets `AUTH__SERVICE_TOKEN` to a fixed value in `pytest_configure`, before the app is imported —
the first step of the setup [Testing → Settings](../../../docs/architecture/testing.md#settings) describes;
`add-test-database` adds the container variables to the same hook. With that, `tests/test_exceptions.py` calls the
real app through `httpx.ASGITransport` for everything that fails before a service touches the database: token,
unknown path, wrong method, body/query/header validation. A small app built with `register_exception_handlers` and
test-only routes covers `ServiceError`, `IntegrityError` (constructed with a fake `orig`) and the 500 handler
(`ASGITransport(raise_app_exceptions=False)`). `tests/core/test_exceptions.py` checks that `ERROR_STATUSES` covers
every `ErrorCode` with the documented status.

## Risks / Trade-offs

- [The bot breaks on 400 instead of 422 and on the new body] → the API is 0.x; the bot is updated to branch on `code`.
- [With `debug=True`, Starlette renders a traceback page instead of calling the 500 handler] → debug is off in every
  deployed environment; documented in the handler.
- [The asyncpg attribute path for the constraint name is an implementation detail of SQLAlchemy] → when no name is
  found the mapping falls back to `CONFLICT`, which is still a correct response; the domain database tests
  (`add-test-database` onwards) cover the real path.
