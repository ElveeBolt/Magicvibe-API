# Proposal

## Why

[Conventions → Pagination](../../../docs/architecture/conventions.md#pagination) limits `page_size` to 1–100, but
`BaseFilterSchema` only enforces the lower bound, so a list request can ask for any number of rows in one page. This
change brings the code to the documented rule.

## What Changes

- `page_size` on every paginated list endpoint accepts values from 1 to 100; a larger value is rejected by request
  validation. The default stays 10.
- The limit is set once, in the shared `BaseFilterSchema` in `core`, so every list endpoint gets it.
- Scope is the schema only. The error response for a rejected value is whatever request validation returns today; the
  documented 400 `VALIDATION_ERROR` body comes with a separate `add-error-codes` change.
- Compatibility: a request with `page_size` above 100 used to succeed and is now rejected. This is stricter input
  validation; the API is on 0.x, where [Versioning](../../../docs/process/versioning.md#before-100) allows it without a
  major bump. The bot must not request more than 100 items per page.

## Capabilities

### New Capabilities

- `api-pagination`: query parameters and response shape shared by every paginated list endpoint, including the
  allowed range of `page_size`.

### Modified Capabilities

None.

## Impact

- Code: `src/magicvibe/core/schemas/base.py` (`BaseFilterSchema`). Every filter schema that subclasses it inherits the
  limit: `user`, `reaction` (matches), `report`, `ban` list endpoints.
- Tests: first tests in the repository, for the shared schema, under `tests/core/`.
- Docs: `docs/architecture/testing.md` gets the location of tests for `core`; `CLAUDE.md` drops `page_size` from the
  "Known drift" list. `conventions.md` already states the rule and does not change.
- No database, migration or dependency changes.
