# Spec Delta

## ADDED Requirements

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
