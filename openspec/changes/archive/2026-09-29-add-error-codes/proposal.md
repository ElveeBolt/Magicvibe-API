# Proposal

## Why

[Errors](../../../docs/architecture/errors.md) defines one error body with a stable `code` that the bot branches on,
and 400 `VALIDATION_ERROR` for requests that fail the schema. Today the API returns only `{"detail": ...}`, request
validation returns FastAPI's 422, a wrong service token returns a bare 401, and a deleted account returns 410 — so the
bot cannot tell one failure from another without parsing English text. This change brings the error contract to the
documented one. It comes first because every later change raises its own codes on top of it.

## What Changes

- Every error response has the body `{"code", "detail", ...extra}`; the status and `code` come from the
  [code table](../../../docs/architecture/errors.md#codes).
- Request validation returns **400** `VALIDATION_ERROR` with an `errors` list of `{field, type, message}` instead of
  422 with FastAPI's `detail` list. **BREAKING** for the bot (status and body change); allowed on 0.x
  ([Versioning → Before 1.0.0](../../../docs/process/versioning.md#before-100)).
- A missing or wrong service token returns 401 `INVALID_SERVICE_TOKEN`.
- Framework errors use the same body: unknown path 404 `NOT_FOUND`, wrong method 405 `METHOD_NOT_ALLOWED`, an
  unhandled exception 500 `INTERNAL_ERROR` with `request_id` and no internals.
- A database constraint violation is mapped by constraint name: the reaction pair → 409 `ALREADY_REACTED`, the
  active-ban partial unique index → 409 `BAN_ALREADY_ACTIVE`, anything else → 409 `CONFLICT`.
- Existing rejections get their documented codes: unknown acting user `USER_NOT_FOUND`, banned acting user
  `USER_BANNED` with `ban: {reason, comment}` (instead of the whole ban record), reacting to or reporting oneself
  `SELF_ACTION`, a repeated reaction `ALREADY_REACTED`, a second active ban `BAN_ALREADY_ACTIVE`, browsing without a
  profile 409 `PROFILE_REQUIRED` (was 400).
- **BREAKING**: the 410 `Gone` response is removed. A soft-deleted acting user now gets 404 `USER_NOT_FOUND`, which is
  what the documented hard delete produces; the soft delete itself is removed by a later change
  (`hard-delete-accounts`).
- Every code from the table exists in the `ErrorCode` enum. Codes whose rules are not built yet
  (`PREFERENCES_REQUIRED`, `PHOTO_LIMIT_REACHED`, `DAILY_LIMIT_REACHED`, `PREMIUM_REQUIRED`,
  `PREMIUM_ALREADY_ACTIVE`, `TARGET_USER_BANNED`) are only declared here; the changes that build those rules raise
  them.

## Capabilities

### New Capabilities

- `api-errors`: the error response body, the general and account codes with their statuses, request validation
  errors, framework and unexpected errors, database constraint mapping, and the codes of the business rejections that
  already exist.

### Modified Capabilities

None. `api-pagination` refers to "a request validation error" without fixing its status, so its requirements do not
change.

## Impact

- Code: `src/magicvibe/core/exceptions.py` (`ErrorCode`, statuses, exceptions), `src/magicvibe/exceptions.py`
  (handlers), `src/magicvibe/dependencies.py` (service token), `src/magicvibe/middlewares/logging_middleware.py`
  (request ID reachable from the 500 handler), and the services that raise: `user`, `reaction`, `report`, `ban`,
  `discovery`, plus `core/database/alchemy/service.py`.
- API: statuses and bodies of every error response change (see above).
- Tests: no database yet — handlers are tested through the real app with `httpx`; `tests/conftest.py` sets a fixed
  `AUTH__SERVICE_TOKEN` before the app is imported, as [Testing → Settings](../../../docs/architecture/testing.md#settings)
  describes.
- Docs: `errors.md` states that `field` omits the request part (`body`, `query`, …); `testing.md` layout gets
  `tests/conftest.py` and the app-level `tests/test_exceptions.py`; `CLAUDE.md` drops the error-codes item from
  "Known drift".
- No database, migration or dependency changes.
