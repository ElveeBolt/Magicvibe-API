# reactions Specification

## Purpose

Defines how the acting user reacts to another user — like, superlike or dislike, optionally with a message — and when
a reaction completes a match.

## Requirements

### Requirement: Reacting to a user

`POST /reactions` SHALL record a reaction of the acting user to `to_user_id`: `action` `like` or `dislike`,
`is_super` (only with `like`) and an optional `message` (only with `like`, 1–500 characters after trimming). It SHALL
return 201 with the reaction and `match` (null unless this reaction completed a match). A reaction SHALL NOT be changed
or repeated.

#### Scenario: Like with a message

- **WHEN** the acting user likes another user with a message
- **THEN** the response is 201 with the reaction, its message, and `match` null

#### Scenario: Superlike

- **WHEN** the acting user likes another user with `is_super` true
- **THEN** the response is 201 with `is_super` true

#### Scenario: Dislike with a message

- **WHEN** the acting user dislikes another user with a message
- **THEN** the response is 400 with `code` `VALIDATION_ERROR`

#### Scenario: Empty message

- **WHEN** a like has a message that is empty or only spaces
- **THEN** the response is 400 with `code` `VALIDATION_ERROR` and an `errors` entry for `message`

#### Scenario: Repeated reaction

- **WHEN** the acting user reacts again to a user they already reacted to
- **THEN** the response is 409 with `code` `ALREADY_REACTED`

#### Scenario: Reaction to oneself

- **WHEN** the acting user reacts to their own user ID
- **THEN** the response is 400 with `code` `SELF_ACTION`

#### Scenario: Unknown or banned target

- **WHEN** the acting user reacts to a user ID no account has, or to a banned user
- **THEN** the response is 404 with `code` `NOT_FOUND` and no reaction is stored

### Requirement: A mutual like creates a match

When a like (with or without `is_super`) meets a like from the other user in the opposite direction, the API SHALL
create exactly one match for the two users in the same transaction and return it as `match` of the reaction that
completed the pair. A dislike SHALL NOT create a match.

#### Scenario: Like back

- **WHEN** user A liked user B and user B now likes user A
- **THEN** the response to B's like has `match` with A as the partner, and one match exists for the pair

#### Scenario: Superlike back

- **WHEN** user A superliked user B and user B now likes user A
- **THEN** the response has a `match`

#### Scenario: Dislike back

- **WHEN** user A liked user B and user B now dislikes user A
- **THEN** the response has `match` null and no match exists

#### Scenario: Opposite likes at the same time

- **WHEN** user A likes user B and user B likes user A at the same time
- **THEN** exactly one match exists for the pair and exactly one of the two responses carries it

### Requirement: Daily limits

Before recording a like or a superlike, `POST /reactions` SHALL check the acting user's effective plan at that moment.
A superlike on a plan whose daily superlike limit is 0 SHALL return 403 `PREMIUM_REQUIRED`. Otherwise, when the acting
user has already made as many likes (without `is_super`) — or superlikes, for a superlike — since the last midnight
Europe/Kyiv as the plan allows, the API SHALL return 429 `DAILY_LIMIT_REACHED` with `limit_type` (`like` or
`superlike`), `resets_at` (the next midnight Europe/Kyiv, in UTC) and a `Retry-After` header with the whole seconds
until `resets_at`, rounded up. Nothing SHALL be recorded in either case. Dislikes SHALL never be limited, and a
superlike SHALL count only toward the superlike limit. Parallel reactions of one user SHALL NOT exceed a limit.

#### Scenario: Last like of the day

- **WHEN** a free user who liked 4 users today likes a fifth
- **THEN** the response is 201

#### Scenario: Like limit used up

- **WHEN** a free user who liked 5 users today likes another
- **THEN** the response is 429 with `code` `DAILY_LIMIT_REACHED`, `limit_type` `like`, `resets_at` at the next
  midnight Europe/Kyiv and a matching `Retry-After`

#### Scenario: Superlike on the free plan

- **WHEN** a free user superlikes another user
- **THEN** the response is 403 with `code` `PREMIUM_REQUIRED`

#### Scenario: Superlike limit used up

- **WHEN** a premium user who superliked 5 users today superlikes another
- **THEN** the response is 429 with `limit_type` `superlike`

#### Scenario: Superlikes do not use likes

- **WHEN** a premium user who superliked 5 users today likes another user
- **THEN** the response is 201

#### Scenario: Dislikes are unlimited

- **WHEN** a free user who liked 5 users today dislikes another
- **THEN** the response is 201

#### Scenario: Likes from before midnight

- **WHEN** a free user's 5 likes were made just before the last midnight Europe/Kyiv
- **THEN** a like now returns 201

#### Scenario: Premium ended during the day

- **WHEN** a user liked 10 users today on premium and premium has ended
- **THEN** a like returns 429 with `limit_type` `like`

#### Scenario: Repeated reaction at the limit

- **WHEN** a free user at the like limit likes a user they already reacted to
- **THEN** the response is 409 with `code` `ALREADY_REACTED`

#### Scenario: Parallel likes at the limit

- **WHEN** a free user who liked 4 users today sends two likes at the same time
- **THEN** exactly one returns 201 and the other 429
