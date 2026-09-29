# Proposal

## Why

[PRD → Accounts](../../../docs/prd.md#61-accounts) and [Data model → `users`](../../../docs/architecture/models.md#users)
define account deletion as a permanent hard delete, a banned user whose Telegram data is left unchanged on `/start`,
a `status` that only the `ban` domain changes, and a `last_seen_at` kept current. The code does a soft delete
(`UserStatus.DELETED`, `deleted_at`, `POST /users/{id}/restore`), lets `PATCH /users/{id}` set any status, refreshes a
banned user's Telegram data on `POST /users`, and never updates `last_seen_at`.

## What Changes

- `DELETE /users/{user_id}` deletes the `users` row; every row of the user in every table goes with it through
  `ON DELETE CASCADE`. A banned user cannot be deleted: 403 `USER_BANNED`. The user row is locked
  (`SELECT … FOR UPDATE`) for the check, and ban creation locks it too, so a ban and a deletion cannot interleave.
- **BREAKING**: `POST /users/{user_id}/restore` is removed; so is `PATCH /users/{user_id}` (its only fields were
  `status` and `deleted_at`). `deleted_at` leaves the user response, and `deleted` leaves `UserStatus`.
- `POST /users` for a banned user returns 403 `USER_BANNED` with the ban and does not update the stored Telegram data.
  After a deletion, `POST /users` with the same Telegram ID creates a new account (201).
- Every request with an acting user updates `last_seen_at` when it is more than a minute old.
- Migrations: `alembic-postgresql-enum` is added so autogenerate handles PostgreSQL enum changes (here: removing
  `deleted` from `user_status_enum`; later changes add enum columns). The migration drops `users.deleted_at` and the
  `deleted` value.
- The API is 0.x, so the removed endpoints and fields are allowed without a major bump
  ([Versioning → Before 1.0.0](../../../docs/process/versioning.md#before-100)).

## Capabilities

### New Capabilities

- `accounts`: registration and refresh of a user by Telegram account, account deletion, account status, and when the
  acting user's last-online time is updated.

### Modified Capabilities

- `api-errors`: the "Deleted acting user" scenario now describes a hard-deleted account (no status involved).

## Impact

- Code: `user` (enums, model, schemas, repository, service, router), `ban/services.py` (locks the user), `alembic/env.py`
  (imports `alembic_postgresql_enum`), a new migration.
- Dependencies: `alembic-postgresql-enum` in the production group (imported by `alembic/env.py`, which runs where
  migrations are applied).
- API: see What Changes. The bot must stop calling `restore` and `PATCH /users/{id}`, and handle 403 `USER_BANNED` on
  `/start`.
- Data: a database that already holds users with status `deleted` must have them deleted by a person before the
  migration is applied (migrations never change data).
- Docs: `CLAUDE.md` drops soft delete from "Known drift". `models.md`, `prd.md` and `glossary.md` already describe the
  target and do not change. `conventions.md` → Migrations gets a line on enum changes.
