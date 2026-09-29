# Tasks

## 1. Codes and exceptions in `core`

- [x] 1.1 In `src/magicvibe/core/exceptions.py` add `ErrorCode(StrEnum)` with every code from
  `docs/architecture/errors.md`, `ERROR_STATUSES` with each code's status, and give `ServiceError` `detail`, `code`,
  `extra`, `headers` and `status_code`; keep `NotFoundError`, `ConflictError`, `BadRequestError`, `ForbiddenError`
  with their default codes, add `UnauthorizedError`, remove `GoneError`; verify `uv run mypy src/magicvibe` fails
  only at the raise sites fixed in group 3
- [x] 1.2 Add `tests/core/test_exceptions.py`: every `ErrorCode` has a status, the statuses equal the table in
  `errors.md` (written out in the test), and each exception class gets its default code and status; verify
  `uv run pytest tests/core` passes

## 2. Handlers, token and request ID

- [x] 2.1 In `src/magicvibe/middlewares/logging_middleware.py` store the request ID in `scope["state"]["request_id"]`
  as well as in structlog contextvars; verify with the 500 test in 2.4
- [x] 2.2 Rewrite `register_exception_handlers` in `src/magicvibe/exceptions.py`: `ServiceError`,
  `RequestValidationError` (400 `VALIDATION_ERROR`, `errors` with `field`/`type`/`message`), `StarletteHTTPException`
  (404/405 and fallbacks), `IntegrityError` (constraint name → `ALREADY_REACTED` / `BAN_ALREADY_ACTIVE` / `CONFLICT`),
  `Exception` (500 `INTERNAL_ERROR` with `request_id`); verify with 2.4
- [x] 2.3 Make `require_service_token` in `src/magicvibe/dependencies.py` raise
  `UnauthorizedError(ErrorCode.INVALID_SERVICE_TOKEN)` with `WWW-Authenticate: Bearer`; verify with 2.4
- [x] 2.4 Add `tests/conftest.py` whose `pytest_configure` sets `AUTH__SERVICE_TOKEN` to a fixed test token (no
  module-level import of `magicvibe`), and `tests/test_exceptions.py` covering the `api-errors` scenarios that need no
  database: missing/wrong token, unknown path, wrong method, body field too long, unknown field, nested field,
  `page_size=101`, a `ServiceError` with extra fields, `IntegrityError` for each mapped name and an unknown one (body
  has no database text), 500 with generated and client `X-Request-ID`; verify `uv run pytest` passes

## 3. Codes at the raise sites

- [x] 3.1 `user/services.py`: `get_acting_user` raises `USER_NOT_FOUND` for unknown and deleted users, `USER_BANNED`
  with `ban: {reason, comment}`, and no longer writes `status`; `soft_delete` of a banned user raises `USER_BANNED`;
  `update_preference` raises `VALIDATION_ERROR` with one `errors` entry; verify with mypy and the API test in 3.4
- [x] 3.2 `reaction/services.py` (`SELF_ACTION`, `NOT_FOUND`, `ALREADY_REACTED`), `report/services.py`
  (`SELF_ACTION`, `NOT_FOUND`), `ban/services.py` (`NOT_FOUND`, `BAN_ALREADY_ACTIVE`, `CONFLICT`),
  `discovery/services.py` (`PROFILE_REQUIRED`), `core/database/alchemy/service.py` (`NOT_FOUND`); verify
  `grep -rn "Error(" src/magicvibe --include=services.py` shows a code at every raise without a class default
- [x] 3.3 Add a test that the `USER_BANNED` extra built from a ban has exactly `reason` and `comment`, and one that
  `DiscoveryService.get_next_candidate` for a viewer without a profile raises `PROFILE_REQUIRED` (no database is
  touched before that check); verify `uv run pytest` passes
- [x] 3.4 Add an API test that `X-Telegram-User-Id` that is not an integer returns 400 `VALIDATION_ERROR` with
  `field` `X-Telegram-User-Id` or its lowercase form as the framework reports it; verify `uv run pytest` passes

## 4. Docs

- [x] 4.1 In `docs/architecture/errors.md` → Validation errors, state that `field` omits the request part (`body`,
  `query`, `path`, `header`) and is empty for a whole-object error; verify the section says so
- [x] 4.2 In `docs/architecture/testing.md` → Layout, add `tests/test_exceptions.py` (app-level error handlers);
  verify the tree and the bullet list mention it
- [x] 4.3 In `CLAUDE.md` remove the "no `ErrorCode` or `code` in error bodies, and validation returns 422 instead of
  400" item from "Known drift" and update "How a request flows" if it mentions `GoneError`; verify neither remains

## 5. Integration checks

- [x] 5.1 Run `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`,
  `uv run mypy src/magicvibe` and `npx openspec validate add-error-codes --strict`; all exit 0 and pytest reports
  passed tests
