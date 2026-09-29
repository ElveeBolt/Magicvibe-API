# Proposal

## Why

[PRD → Reports](../../../docs/prd.md#69-reports) says a report always succeeds for the reporter and a repeated report
does not create a second open one; [Data model → `reports`](../../../docs/architecture/models.md#reports) enforces that
with a partial unique index on open reports. [PRD → Bans](../../../docs/prd.md#610-bans) says a ban has no end date.
The code creates a new report on every request, has no such index, and gives bans an optional `expires_at` that makes
a ban silently stop while `users.status` stays `banned` — the user is then neither blocked nor shown.

## What Changes

- `POST /reports`: a report against a user who already has an open report from this reporter returns that report
  with 200 instead of creating another; a new report still returns 201. Reporting a banned user succeeds.
- `reports` gets the partial unique index on `(reporter_id, target_id) WHERE status = 'open'`; the insert relies on it
  (`ON CONFLICT DO NOTHING`), so two simultaneous reports create one.
- `PATCH /reports/{report_id}` accepts only `resolved` or `dismissed` as the new status — reviewing closes a report;
  setting it back to `open` is rejected with 400 `VALIDATION_ERROR`.
- **BREAKING**: `expires_at` is removed from bans (column, create/update/read schemas). A ban is active exactly while
  `lifted_at` is null. Allowed on 0.x.
- One definition of "active ban" in the `ban` repository (the separate `has_unlifted` check goes).
- Visibility effects of a ban outside these domains (matches list, reacting to a banned user) come with
  `add-matches`; discovery already excludes banned users.

## Capabilities

### New Capabilities

- `reports`: filing a report (self-report, repeated report, unknown or banned target) and reviewing it.
- `bans`: creating, lifting and reading bans, the one-active-ban rule and the account status they set.

### Modified Capabilities

None.

## Impact

- Code: `report` (model index, repository, service, schemas, router), `ban` (model, repository, service, schemas), a
  new migration.
- API: `POST /reports` may return 200; `PATCH /reports/{id}` rejects `open`; `expires_at` disappears from ban requests
  and responses.
- Data: bans whose `expires_at` has passed become active again after the migration drops the column; a person lifts
  them first if they should stay ended (migrations never change data). An existing database with duplicate open
  reports must have them closed before the index can be created.
- Docs: none — `prd.md` and `models.md` already describe the target.
