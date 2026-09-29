# Design

## Context

- `UserProfile`: `bio` is `Text NOT NULL`; there is a partial index `ix_user_profiles_discovery` on `(gender,
  birth_date) WHERE is_visible`; no city, no dating goal. `UserPreference`: gender and ages only.
- `UserService.set_profile` calls `get_or_create_preference`, so every user with a profile has default preferences.
- `User` loads `profile`, `telegram`, `preference` with `lazy="joined"`; discovery loads candidates with
  `join(User.profile)` + `contains_eager(User.profile)`.
- `region` domain (previous change) has `RegionCity` and `RegionCityReadSchema`; `uow.region_city` is registered.
- Autogenerate (with `alembic-postgresql-enum`) handles columns, enum types and indexes, but not check constraints on
  an existing table.

## Goals / Non-Goals

**Goals:**

- The profile and preferences match `models.md` column for column; every rule is enforced in the schema and the
  database with the same constant.
- One read gives the bot everything it shows about a profile, including the city name.

**Non-Goals:**

- Discovery filtering by city and goal, `PREFERENCES_REQUIRED` (`align-discovery`).
- Profile images (deferred).

## Decisions

### `DatingGoal` in `user/enums.py`, one enum type for both tables

`DatingGoal(StrEnum)` with the four values; stored as `dating_goal_enum` on `user_profiles.dating_goal` (not null) and
`user_preferences.dating_goal` (null = any), like `user_profile_gender_enum` already is. `alembic-postgresql-enum`
creates the type once before the columns are added.

### The city as a joined relationship

`UserProfile.city` and `UserPreference.city` are `relationship(lazy="joined")` to `RegionCity` (foreign key string
`"cities.id"`, no `ON DELETE`: cities are never deleted). Read schemas use `RegionCityReadSchema` from the `region`
domain, so the city has the same shape everywhere. The user domain importing the region model and schema is a
dependency in one direction only (region knows nothing about users).

*Alternative:* only `city_id`, and the bot resolves it — rejected: the bot would need another request per profile
(and a `GET /cities/{id}` that does not exist) for every shown profile.

### Unknown city → 404 in the service

`UserService` checks `uow.region_city.exists(city_id)` before writing a profile or preferences with a `city_id`, and
raises `NotFoundError("City not found")` (404 `NOT_FOUND`), the same answer as an unknown `target_id` in reports and
reactions. The foreign key stays as the database-side guarantee.

### `bio`

`String(MAX_BIO_LENGTH)` nullable with `CheckConstraint(or_(bio.is_(None), bio != ""), name="bio_not_empty")`. The
`Bio` type already strips and requires one character. Create schema: `bio: Bio | None = None`; update schema:
`bio: Bio | None = None` without `NonNullable`, so `null` clears it. Required fields keep `NonNullable`.

### No preferences on profile save

`set_profile` stops calling `get_or_create_preference`, which is removed. Discovery keeps treating missing
preferences as defaults until `align-discovery` introduces `PREFERENCES_REQUIRED`.

### Migration

Autogenerate on a throwaway container gives: `dating_goal_enum`, the new columns and foreign keys, `bio` type and
nullability, the dropped index. Appended by hand to the same new file, and only this: `op.create_check_constraint(
op.f("ck_user_profiles_bio_not_empty"), "user_profiles", "bio IS NULL OR bio <> ''")` in `upgrade` and the matching
`op.drop_constraint` in `downgrade`. A `test_models.py` test proves the constraint exists under its expected name.

## Risks / Trade-offs

- [`NOT NULL` columns cannot be added to a table with rows] → the person applying the migration deletes development
  profiles first (proposal → Impact).
- [`contains_eager(User.profile)` in discovery plus the joined `city`] → covered by a discovery API test that returns
  a candidate with its city.
- [`bio` `text` → `varchar(500)` fails for longer stored values] → none can exist: the schema always limited it to 500.
