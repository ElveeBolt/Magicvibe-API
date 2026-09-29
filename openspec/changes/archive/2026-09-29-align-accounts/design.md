# Design

## Context

- `UserRepository.upsert_by_telegram_id` takes a transaction-level advisory lock on the Telegram ID, then updates the
  Telegram data of an existing user or creates a new one; the service restores soft-deleted users afterwards.
- `User` loads `profile`, `telegram` and `preference` with `lazy="joined"` (outer joins).
- `BanService.create` reads the user, checks for an unlifted ban, inserts the ban and sets `status = banned`, without
  locking the user.
- Every foreign key to `users.id` / `user_profiles.id` already has `ON DELETE CASCADE` (first migration).
- Alembic autogenerate does not compare PostgreSQL enum values, so removing `deleted` from `user_status_enum` would
  not appear in a generated migration.

## Goals / Non-Goals

**Goals:**

- Deletion relies on the database cascade, not on ORM cascades or per-table deletes.
- The banned check and the delete (or the ban insert) happen under one row lock.

**Non-Goals:**

- Photo files in S3 (the S3 deletion before the row delete comes with `add-profile-images`, which is deferred).
- An endpoint shape change (for example deleting through the acting user): the existing `/users/{user_id}` paths
  stay.

## Decisions

### Hard delete with a Core `DELETE` after a row lock

`UserRepository.get_for_update(id_)` selects the user with `with_for_update(of=User)`: the joined eager loads are
outer joins, and PostgreSQL rejects `FOR UPDATE` on the nullable side of one, so the lock is limited to `users`. The
service checks `status`; if `banned`, it reads the active ban and raises `USER_BANNED`; otherwise
`AlchemyRepository.delete(id_)` issues `DELETE FROM users WHERE id = …` and the database cascade removes the rest.
*Alternative:* `session.delete(user)` with ORM cascades — rejected, it loads and deletes children one by one and
covers only the relationships the model declares (not reactions, reports or bans).

`BanService.create` uses the same `get_for_update` before its unlifted-ban check, so a concurrent ban and delete are
serialized on the user row: whichever runs second sees the other's result (a `banned` status, or no user → 404).

### Registration decides in the service

The repository keeps the advisory lock and gets split into `lock_telegram_id`, `get_by_telegram_id`,
`create_with_telegram` and `update_telegram`; `UserService.upsert` decides: no user → create (201); banned →
`USER_BANNED` with the ban, nothing written; otherwise update the Telegram data (200). The business decision moves out
of the repository, as [Conventions → Layers](../../../docs/architecture/conventions.md#layers) requires.

### `last_seen_at` in the acting-user dependency

`UserService.get_acting_user` (already one unit of work per request) calls
`UserRepository.touch_last_seen(user_id)`: `UPDATE users SET last_seen_at = now() WHERE id = … AND last_seen_at <
now() - LAST_SEEN_UPDATE_INTERVAL`, with `LAST_SEEN_UPDATE_INTERVAL = timedelta(minutes=1)` in `user/constants.py`.
One conditional statement, no read-modify-write race, at most one write per minute per user. It runs after the
banned check, so a banned user's row is never touched. `updated_at` follows through its `onupdate`, which matches
"updated on every change".

*Alternative:* a middleware — rejected, it would need its own database session and would run for requests without an
acting user.

### Enum migrations with `alembic-postgresql-enum`

`uv add alembic-postgresql-enum` and `import alembic_postgresql_enum` in `alembic/env.py`. Autogenerate then emits
`op.sync_enum_values(...)` for changed values and creates enum types for new columns. This keeps the migrations rule
("never write a migration by hand") intact for this and the later changes that add enum columns (`DatingGoal`,
`PlanCode`, `RegionCodeType`). It goes into the production dependencies because `alembic/env.py` imports it wherever
migrations run.

### Tests and time

The test transaction fixes `now()` for the whole test, so the `last_seen_at` tests set the stored value relative to
the database's `now()` (`now() - interval '2 minutes'` / `'10 seconds'`), make one request and compare. No real time
passes.

## Risks / Trade-offs

- [A database with `status = 'deleted'` rows cannot drop the enum value] → the person applying the migration deletes
  those users first (noted in the proposal); the test database starts empty.
- [`alembic-postgresql-enum` rewrites the enum type when a value is removed (create new type, cast, drop old)] → the
  migration runs in one transaction on PostgreSQL; tested by the test session applying it.
- [`FOR UPDATE` on `users` adds a lock to deletion and ban creation] → both are rare, single-row operations.
