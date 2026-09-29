# Proposal

## Why

[Conventions → Schemas](../../../docs/architecture/conventions.md#schemas) says every schema forbids unknown fields
(`extra="forbid"`, inherited from `BaseSchema`). `BaseUpdateSchema`, the base of every `PATCH` body, derives from
`BaseModel` instead, so a `PATCH` with a misspelled or removed field (for example `expires_at` on a ban) succeeds and
the field is silently ignored.

## What Changes

- `BaseUpdateSchema` derives from `BaseSchema`, so every `PATCH` body (`/users/{id}/profile`,
  `/users/{id}/preferences`, `/users/{id}/telegram`, `/reports/{id}`, `/bans/{id}`) rejects unknown fields with 400
  `VALIDATION_ERROR`, `type` `extra_forbidden`.
- Stricter input: a request that used to succeed with an ignored field is now rejected. Allowed on 0.x.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `api-errors`: the "Validation errors" requirement states that it covers partial-update bodies too, with a scenario.

## Impact

- Code: `src/magicvibe/core/schemas/base.py` only.
- Tests: `tests/core/test_schemas.py` (the base class), an API test on `PATCH /reports/{id}` and `PATCH /bans/{id}`.
- Docs: none — `conventions.md` already states the rule.
