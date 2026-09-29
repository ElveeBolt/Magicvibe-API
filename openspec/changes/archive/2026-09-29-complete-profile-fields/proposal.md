# Proposal

## Why

[PRD → Profile](../../../docs/prd.md#62-profile) and [PRD → Discovery preferences](../../../docs/prd.md#65-discovery-preferences)
require a city and one dating goal in every profile, an optional bio, and preferences for city and dating goal (each
may be "any"); [Data model](../../../docs/architecture/models.md#user_profiles) defines `city_id`, `dating_goal`
(`DatingGoal`), a nullable `bio` with `bio_not_empty`, and preferences with nullable `city_id` / `dating_goal`. The
code has no city and no dating goal, requires `bio` (`text`, not null), has an extra discovery index, and silently
creates default preferences when the profile is saved, although preferences must be set by the user.

## What Changes

- Profile: required `city_id` (a city from `regions`/`cities`) and `dating_goal` (`relationship`, `friendship`,
  `casual`, `chatting`); `bio` optional (`null` when missing, never empty; `PATCH` may clear it with `null`), stored
  as `varchar(500)` with the `bio_not_empty` check. The profile response carries `city_id` and the city
  in the same shape as `GET /regions/{region_id}/cities` returns it.
- Preferences: optional `city_id` and `dating_goal` (`null` = any), next to gender and the age range. The response
  carries the city when one is set.
- An unknown `city_id` in a profile or preferences body returns 404 `NOT_FOUND`.
- **BREAKING**: `PUT /users/{id}/profile` requires `city_id` and `dating_goal`, and no longer creates preferences as a
  side effect; the bot sets them with `PUT /users/{id}/preferences`. Allowed on 0.x.
- The `ix_user_profiles_discovery` index, which `models.md` does not list, is dropped.
- Migration: autogenerate for columns, types and indexes; the `bio_not_empty` check is appended by hand to the
  generated file, because autogenerate does not compare check constraints of existing tables. The migrations rule and
  `conventions.md` are updated to allow exactly that.
- Two-way fit on city and dating goal in discovery, and `PREFERENCES_REQUIRED`, come with `align-discovery`.

## Capabilities

### New Capabilities

- `profile`: creating, reading and changing the profile, its required and optional fields.
- `preferences`: setting, reading and changing discovery preferences.

### Modified Capabilities

None.

## Impact

- Code: `user` (enums, constants, models, schemas, types, repository, service), a new migration.
- Data: existing `user_profiles` rows cannot get the new `NOT NULL` columns; the person applying the migration deletes
  them first (development data only).
- Docs: `.claude/rules/conventional-migrations.md` and `conventions.md` → Migrations (check constraints appended by
  hand); `CLAUDE.md` "Known drift" drops `DatingGoal`.
