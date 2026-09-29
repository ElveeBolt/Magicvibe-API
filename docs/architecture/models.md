# Data model

All tables of the MagicVibe API. All foreign keys to `users.id` and `user_profiles.id` use `ON DELETE CASCADE`. Foreign
keys to `regions.id` and `cities.id` have no `ON DELETE` action: regions and cities are never deleted. Timestamps are
`timestamptz` in UTC.

Each table has a column table. Primary keys, single-column unique constraints and foreign keys are shown there. Every
other constraint and index is listed in the table's **Constraints** table:

| Field     | Meaning                                                                                                   |
|-----------|-----------------------------------------------------------------------------------------------------------|
| `Name`    | Constraint name for checks and multi-column unique constraints; `—` for indexes (named by the convention) |
| `Kind`    | `check`, `unique`, `index`, `partial unique` or `partial index`                                           |
| `Columns` | Columns in index order                                                                                    |
| `Rule`    | Exact SQL: the check expression, or the `WHERE` condition of a partial index; for a plain index, its use  |

Constant names in `Rule` stand for their values in the domain's `constants.py`. A table with no Constraints table has
no constraints besides its column table. All of them are enforced by the database, not only in code.

This document is the source of truth for the data model. SQLAlchemy models and migrations follow it; when they differ,
the code is changed to match this document.

## `user` domain

### `users`

| Column         | Type                             | Nullable | Unique | Foreign key | Default  | Notes                                                                                                                 |
|----------------|----------------------------------|----------|--------|-------------|----------|-----------------------------------------------------------------------------------------------------------------------|
| `id`           | bigint                           | false    | true   | —           | —        | primary key                                                                                                           |
| `status`       | enum [`UserStatus`](#userstatus) | false    | false  | —           | `active` |                                                                                                                       |
| `last_seen_at` | timestamptz                      | false    | false  | —           | `now()`  | shown to others as last online; updated on every request where this user is the acting user, at most once per minute  |
| `created_at`   | timestamptz                      | false    | false  | —           | `now()`  |                                                                                                                       |
| `updated_at`   | timestamptz                      | false    | false  | —           | `now()`  | updated on every change                                                                                               |

Relationships: `telegram`, `profile`, `preference` (one-to-one).

`status` mirrors the active ban in `bans`: the `ban` domain sets it to `banned` when it creates a ban and back to
`active` when it lifts one, in the same transaction. No other code changes it. A ban deletes nothing: the user's rows
stay unchanged and are hidden from other users while the status is `banned`.

Account deletion is a hard delete of the `users` row. Every foreign key to `users.id` and `user_profiles.id` is
`ON DELETE CASCADE`, so all of the user's rows in every table are deleted with it. Photo files in S3 are not covered by
the cascade: the service deletes them before deleting the row. A user with `status = banned` cannot be deleted. See
[PRD → Accounts](../prd.md#61-accounts).

### `user_telegrams`

| Column          | Type        | Nullable | Unique | Foreign key | Default | Notes                                               |
|-----------------|-------------|----------|--------|-------------|---------|-----------------------------------------------------|
| `id`            | bigint      | false    | true   | —           | —       | primary key                                         |
| `user_id`       | bigint      | false    | true   | `users.id`  | —       |                                                     |
| `telegram_id`   | bigint      | false    | true   | —           | —       |                                                     |
| `first_name`    | string(64)  | false    | false  | —           | —       |                                                     |
| `last_name`     | string(64)  | true     | false  | —           | —       |                                                     |
| `username`      | string(32)  | true     | false  | —           | —       |                                                     |
| `language_code` | string(8)   | true     | false  | —           | —       |                                                     |
| `is_premium`    | bool        | false    | false  | —           | `false` | Telegram Premium flag, unrelated to MagicVibe plans |
| `created_at`    | timestamptz | false    | false  | —           | `now()` |                                                     |
| `updated_at`    | timestamptz | false    | false  | —           | `now()` | updated on every change                             |

### `user_profiles`

| Column        | Type                                           | Nullable | Unique | Foreign key | Default | Notes                                                                     |
|---------------|------------------------------------------------|----------|--------|-------------|---------|---------------------------------------------------------------------------|
| `id`          | bigint                                         | false    | true   | —           | —       | primary key                                                               |
| `user_id`     | bigint                                         | false    | true   | `users.id`  | —       |                                                                           |
| `name`        | string(`MAX_PROFILE_NAME_LENGTH`)              | false    | false  | —           | —       |                                                                           |
| `birth_date`  | date                                           | false    | false  | —           | —       | age `MIN_PROFILE_AGE`–`MAX_PROFILE_AGE` inclusive; schema only, see below |
| `gender`      | enum [`UserProfileGender`](#userprofilegender) | false    | false  | —           | —       |                                                                           |
| `bio`         | string(`MAX_BIO_LENGTH`)                       | true     | false  | —           | —       |                                                                           |
| `city_id`     | bigint                                         | false    | false  | `cities.id` | —       |                                                                           |
| `dating_goal` | enum [`DatingGoal`](#datinggoal)               | false    | false  | —           | —       |                                                                           |
| `is_visible`  | bool                                           | false    | false  | —           | `true`  | `false` = hidden profile, excluded from discovery only                    |
| `created_at`  | timestamptz                                    | false    | false  | —           | `now()` |                                                                           |
| `updated_at`  | timestamptz                                    | false    | false  | —           | `now()` | updated on every change                                                   |

Relationships: `images` (one-to-many).

Constraints:

| Name            | Kind  | Columns | Rule                       |
|-----------------|-------|---------|----------------------------|
| `bio_not_empty` | check | `bio`   | `bio IS NULL OR bio <> ''` |

The age rule on `birth_date` has no database check: it depends on the current date, and a `CHECK` constraint cannot
use `now()`. It is the only rule enforced in the schema only.

A row exists only when every required field is filled, because required columns cannot be null; `bio` is the only
optional one. A missing bio is always null, never an empty string. So a user with a `user_profiles` row has a complete
profile; without it the user is not shown in discovery and cannot use it.

### `user_preferences`

| Column        | Type                                           | Nullable | Unique | Foreign key | Default           | Notes                   |
|---------------|------------------------------------------------|----------|--------|-------------|-------------------|-------------------------|
| `id`          | bigint                                         | false    | true   | —           | —                 | primary key             |
| `user_id`     | bigint                                         | false    | true   | `users.id`  | —                 |                         |
| `gender`      | enum [`UserProfileGender`](#userprofilegender) | true     | false  | —           | —                 | null = any gender       |
| `min_age`     | smallint                                       | false    | false  | —           | `MIN_PROFILE_AGE` |                         |
| `max_age`     | smallint                                       | false    | false  | —           | `MAX_PROFILE_AGE` |                         |
| `city_id`     | bigint                                         | true     | false  | `cities.id` | —                 | null = any city         |
| `dating_goal` | enum [`DatingGoal`](#datinggoal)               | true     | false  | —           | —                 | null = any goal         |
| `created_at`  | timestamptz                                    | false    | false  | —           | `now()`           |                         |
| `updated_at`  | timestamptz                                    | false    | false  | —           | `now()`           | updated on every change |

Constraints:

| Name         | Kind  | Columns              | Rule                                                        |
|--------------|-------|----------------------|-------------------------------------------------------------|
| `age_range`  | check | `min_age`, `max_age` | `min_age <= max_age`                                        |
| `age_bounds` | check | `min_age`, `max_age` | `min_age >= MIN_PROFILE_AGE AND max_age <= MAX_PROFILE_AGE` |

### `user_profile_images`

| Column         | Type        | Nullable | Unique | Foreign key        | Default | Notes                                         |
|----------------|-------------|----------|--------|--------------------|---------|-----------------------------------------------|
| `id`           | bigint      | false    | true   | —                  | —       | primary key                                   |
| `profile_id`   | bigint      | false    | false  | `user_profiles.id` | —       |                                               |
| `s3_key`       | string(255) | false    | true   | —                  | —       | non-guessable                                 |
| `content_type` | string(32)  | false    | false  | —                  | —       |                                               |
| `size_bytes`   | integer     | false    | false  | —                  | —       | informational; size is not limited by the API |
| `created_at`   | timestamptz | false    | false  | —                  | `now()` |                                               |

Constraints:

| Name | Kind  | Columns      | Rule                |
|------|-------|--------------|---------------------|
| —    | index | `profile_id` | photos of a profile |

Photos belong to the profile, so they can be added only after the profile exists. A profile has from zero to
`MAX_PROFILE_IMAGES` photos.

## `region` domain

Filled only by `data/regions/load.py` (repository root), which a developer runs manually; see
[Regions data](./region_data.md). Regions and cities are never deleted or deactivated. Files: `region/models/region.py`,
`region/models/region_city.py`.

### `regions`

| Column         | Type                                     | Nullable | Unique | Foreign key | Default | Notes                    |
|----------------|------------------------------------------|----------|--------|-------------|---------|--------------------------|
| `id`           | bigint                                   | false    | true   | —           | —       | primary key              |
| `katotth_code` | string(19)                               | false    | true   | —           | —       | `UA` + 17 digits         |
| `name`         | string(100)                              | false    | false  | —           | —       | Ukrainian, as in KATOTTH |
| `name_en`      | string(100)                              | false    | false  | —           | —       | Latin, see below         |
| `code_type`    | enum [`RegionCodeType`](#regioncodetype) | false    | false  | —           | —       |                          |

`name_en` is the Latin transliteration of `name` by the official Ukrainian rules (Resolution of the Cabinet of
Ministers of Ukraine No. 55 of 27.01.2010): KATOTTH itself has no English names. The same applies to `cities`.

### `cities`

| Column         | Type        | Nullable | Unique | Foreign key  | Default | Notes                    |
|----------------|-------------|----------|--------|--------------|---------|--------------------------|
| `id`           | bigint      | false    | true   | —            | —       | primary key              |
| `region_id`    | bigint      | false    | false  | `regions.id` | —       |                          |
| `katotth_code` | string(19)  | false    | true   | —            | —       | `UA` + 17 digits         |
| `name`         | string(100) | false    | false  | —            | —       | Ukrainian, as in KATOTTH |
| `name_en`      | string(100) | false    | false  | —            | —       | Latin, see below         |

Constraints:

| Name | Kind  | Columns     | Rule               |
|------|-------|-------------|--------------------|
| —    | index | `region_id` | cities of a region |

## `reaction` domain

### `reactions`

| Column         | Type                                     | Nullable | Unique | Foreign key | Default | Notes                     |
|----------------|------------------------------------------|----------|--------|-------------|---------|---------------------------|
| `id`           | bigint                                   | false    | true   | —           | —       | primary key               |
| `from_user_id` | bigint                                   | false    | false  | `users.id`  | —       |                           |
| `to_user_id`   | bigint                                   | false    | false  | `users.id`  | —       |                           |
| `action`       | enum [`ReactionAction`](#reactionaction) | false    | false  | —           | —       |                           |
| `is_super`     | bool                                     | false    | false  | —           | `false` | `true` only with `like`   |
| `message`      | string(`MAX_MESSAGE_LENGTH`)             | true     | false  | —           | —       | not null only with `like` |
| `created_at`   | timestamptz                              | false    | false  | —           | `now()` |                           |

Constraints:

| Name                   | Kind   | Columns                                            | Rule                                 |
|------------------------|--------|----------------------------------------------------|--------------------------------------|
| `uq_reaction_pair`     | unique | `from_user_id`, `to_user_id`                       | —                                    |
| `not_self`             | check  | `from_user_id`, `to_user_id`                       | `from_user_id <> to_user_id`         |
| `super_only_on_like`   | check  | `action`, `is_super`                               | `NOT is_super OR action = 'like'`    |
| `message_only_on_like` | check  | `action`, `message`                                | `message IS NULL OR action = 'like'` |
| `message_not_empty`    | check  | `message`                                          | `message IS NULL OR message <> ''`   |
| —                      | index  | `to_user_id`                                       | reactions received by a user         |
| —                      | index  | `from_user_id`, `action`, `is_super`, `created_at` | daily limit counting                 |

A missing message is always null, never an empty string.

### `matches`

| Column       | Type        | Nullable | Unique | Foreign key | Default | Notes                      |
|--------------|-------------|----------|--------|-------------|---------|----------------------------|
| `id`         | bigint      | false    | true   | —           | —       | primary key                |
| `user_a_id`  | bigint      | false    | false  | `users.id`  | —       | the smaller of the two ids |
| `user_b_id`  | bigint      | false    | false  | `users.id`  | —       | the larger of the two ids  |
| `created_at` | timestamptz | false    | false  | —           | `now()` |                            |

Constraints:

| Name            | Kind   | Columns                  | Rule                             |
|-----------------|--------|--------------------------|----------------------------------|
| `uq_match_pair` | unique | `user_a_id`, `user_b_id` | —                                |
| `ordered_pair`  | check  | `user_a_id`, `user_b_id` | `user_a_id < user_b_id`          |
| —               | index  | `user_b_id`              | matches where the user is second |

Storing the pair in a fixed order makes it unique in both directions and also rules out a match with oneself.

A match exists exactly when two `like` reactions (`is_super` does not matter) connect the same users in opposite
directions. The like that completes the pair creates the `matches` row in the same transaction.

## `subscription` domain

Plans are not stored in the database: they are constants in `subscription/constants.py` (see
[Plan constants](./plan_constants.md)). The only table of this domain is `subscriptions`.

### `subscriptions`

| Column       | Type                         | Nullable | Unique | Foreign key | Default | Notes                                                             |
|--------------|------------------------------|----------|--------|-------------|---------|-------------------------------------------------------------------|
| `id`         | bigint                       | false    | true   | —           | —       | primary key                                                       |
| `user_id`    | bigint                       | false    | false  | `users.id`  | —       |                                                                   |
| `plan`       | enum [`PlanCode`](#plancode) | false    | false  | —           | —       |                                                                   |
| `starts_at`  | timestamptz                  | false    | false  | —           | `now()` | set only by the database default; never taken from the API        |
| `expires_at` | timestamptz                  | false    | false  | —           | —       | `starts_at` + the plan's `duration_days`; set to now to end early |
| `comment`    | string(`MAX_COMMENT_LENGTH`) | true     | false  | —           | —       | why it was granted                                                |
| `created_at` | timestamptz                  | false    | false  | —           | `now()` |                                                                   |
| `updated_at` | timestamptz                  | false    | false  | —           | `now()` | updated on every change                                           |

Constraints:

| Name                  | Kind  | Columns                   | Rule                        |
|-----------------------|-------|---------------------------|-----------------------------|
| `expires_after_start` | check | `starts_at`, `expires_at` | `expires_at > starts_at`    |
| `paid_plan_only`      | check | `plan`                    | `plan <> 'free'`            |
| —                     | index | `user_id`, `expires_at`   | current subscription lookup |

Free users have no subscription row: the free plan applies when there is no current subscription.

A subscription is current while `starts_at <= now() < expires_at`. At most one current subscription per user.

## `report` domain

### `reports`

| Column        | Type                                 | Nullable | Unique | Foreign key | Default | Notes                   |
|---------------|--------------------------------------|----------|--------|-------------|---------|-------------------------|
| `id`          | bigint                               | false    | true   | —           | —       | primary key             |
| `reporter_id` | bigint                               | false    | false  | `users.id`  | —       |                         |
| `target_id`   | bigint                               | false    | false  | `users.id`  | —       |                         |
| `reason`      | enum [`ReportReason`](#reportreason) | false    | false  | —           | —       |                         |
| `comment`     | string(`MAX_COMMENT_LENGTH`)         | true     | false  | —           | —       |                         |
| `status`      | enum [`ReportStatus`](#reportstatus) | false    | false  | —           | `open`  |                         |
| `created_at`  | timestamptz                          | false    | false  | —           | `now()` |                         |
| `updated_at`  | timestamptz                          | false    | false  | —           | `now()` | updated on every change |

Constraints:

| Name       | Kind           | Columns                    | Rule                       |
|------------|----------------|----------------------------|----------------------------|
| `not_self` | check          | `reporter_id`, `target_id` | `reporter_id <> target_id` |
| —          | partial unique | `reporter_id`, `target_id` | `status = 'open'`          |
| —          | index          | `reporter_id`              | reports filed by a user    |
| —          | index          | `target_id`                | reports against a user     |
| —          | index          | `status`, `created_at`     | review queue               |

The partial unique index allows one open report per reporter and target.

## `ban` domain

### `bans`

| Column         | Type                           | Nullable | Unique | Foreign key | Default | Notes                                                        |
|----------------|--------------------------------|----------|--------|-------------|---------|--------------------------------------------------------------|
| `id`           | bigint                         | false    | true   | —           | —       | primary key                                                  |
| `user_id`      | bigint                         | false    | false  | `users.id`  | —       |                                                              |
| `reason`       | enum [`BanReason`](#banreason) | false    | false  | —           | —       |                                                              |
| `comment`      | string(`MAX_COMMENT_LENGTH`)   | true     | false  | —           | —       |                                                              |
| `lifted_at`    | timestamptz                    | true     | false  | —           | —       | null = the ban is active; set when an administrator lifts it |
| `lift_comment` | string(`MAX_COMMENT_LENGTH`)   | true     | false  | —           | —       |                                                              |
| `created_at`   | timestamptz                    | false    | false  | —           | `now()` |                                                              |
| `updated_at`   | timestamptz                    | false    | false  | —           | `now()` | updated on every change                                      |

Constraints:

| Name | Kind           | Columns                 | Rule                  |
|------|----------------|-------------------------|-----------------------|
| —    | partial unique | `user_id`               | `lifted_at IS NULL`   |
| —    | index          | `user_id`, `created_at` | ban history of a user |

The partial unique index allows at most one active ban per user.

A ban has no end date: it lasts until an administrator lifts it. Creating and lifting a ban also update
`users.status` (see [`users`](#users)). Lifted bans stay as history; a user can be banned again after a lift.

## Enums

Every enum is a Python `StrEnum` in the domain's `enums.py`, stored with `enum_type(...)`. The value is what is stored
in the database and sent in the API.

### `UserStatus`

Domain: `user`.

| Value    | Meaning                                                                                              |
|----------|------------------------------------------------------------------------------------------------------|
| `active` | The account can be used.                                                                             |
| `banned` | The user has an active ban and is hidden from other users. Set and cleared only by the `ban` domain. |

### `UserProfileGender`

Domain: `user`.

| Value    | Meaning |
|----------|---------|
| `male`   | Male    |
| `female` | Female  |
| `other`  | Other   |

### `DatingGoal`

Domain: `user`.

| Value          | Meaning         |
|----------------|-----------------|
| `relationship` | Relationship    |
| `friendship`   | Friendship      |
| `casual`       | Casual meetings |
| `chatting`     | Just chatting   |

### `RegionCodeType`

Domain: `region`. Values are KATOTTH code types.

| Value | Meaning                                     |
|-------|---------------------------------------------|
| `O`   | Oblast or the Autonomous Republic of Crimea |
| `K`   | City with special status (Kyiv, Sevastopol) |

### `ReactionAction`

Domain: `reaction`.

| Value     | Meaning                                                            |
|-----------|--------------------------------------------------------------------|
| `like`    | Positive reaction. A superlike is a `like` with `is_super = true`. |
| `dislike` | Negative reaction.                                                 |

### `PlanCode`

Domain: `subscription`. Each value matches one plan class in `subscription/constants.py`; see [Plans](../plans.md).

| Value     | Meaning      |
|-----------|--------------|
| `free`    | Free plan    |
| `premium` | Premium plan |

### `ReportReason`

Domain: `report`.

| Value                   | Meaning               |
|-------------------------|-----------------------|
| `spam`                  | Spam                  |
| `harassment`            | Harassment            |
| `fake_profile`          | Fake profile          |
| `inappropriate_content` | Inappropriate content |
| `underage`              | Underage              |
| `scam`                  | Scam                  |
| `other`                 | Other                 |

### `ReportStatus`

Domain: `report`.

| Value       | Meaning                                        |
|-------------|------------------------------------------------|
| `open`      | Not reviewed yet.                              |
| `resolved`  | Reviewed; an administrator marked it resolved. |
| `dismissed` | Reviewed; an administrator dismissed it.       |

### `BanReason`

Domain: `ban`. A separate enum from [`ReportReason`](#reportreason): the two lists may differ. Today they have the same
values.

| Value                   | Meaning               |
|-------------------------|-----------------------|
| `spam`                  | Spam                  |
| `harassment`            | Harassment            |
| `fake_profile`          | Fake profile          |
| `inappropriate_content` | Inappropriate content |
| `underage`              | Underage              |
| `scam`                  | Scam                  |
| `other`                 | Other                 |