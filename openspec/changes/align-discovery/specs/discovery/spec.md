# Spec Delta

## Purpose

Defines how a user browses profiles: who may browse, which users are candidates for them, in which order they come,
and what `GET /discovery/next` returns.

## ADDED Requirements

### Requirement: Who may browse

`GET /discovery/next` SHALL require an acting user with a profile and preferences. Without a profile it SHALL return
409 `PROFILE_REQUIRED`; with a profile but without preferences, 409 `PREFERENCES_REQUIRED`. A hidden acting user SHALL
be able to browse.

#### Scenario: No profile

- **WHEN** an acting user without a profile asks for the next profile
- **THEN** the response is 409 with `code` `PROFILE_REQUIRED`

#### Scenario: No preferences

- **WHEN** an acting user with a profile and no preferences asks for the next profile
- **THEN** the response is 409 with `code` `PREFERENCES_REQUIRED`

#### Scenario: Hidden user browses

- **WHEN** an acting user whose profile is hidden asks for the next profile and a candidate exists
- **THEN** the response is 200 with that candidate

### Requirement: Candidates

A user SHALL be returned to the acting user only when all of these hold: their status is `active`; their profile
exists and is not hidden; they have preferences; they are not the acting user; the acting user has not reacted to
them; their gender, age, city and dating goal match the acting user's preferences; and the acting user's gender, age,
city and dating goal match their preferences. A `null` gender, city or dating goal in preferences SHALL match any
value; ages SHALL match inclusively. A report SHALL NOT exclude anyone.

#### Scenario: Banned user

- **WHEN** the only otherwise fitting user is banned
- **THEN** the response is 200 with `null`

#### Scenario: Hidden profile

- **WHEN** the only otherwise fitting user has hidden their profile
- **THEN** the response is 200 with `null`

#### Scenario: Candidate without preferences

- **WHEN** the only otherwise fitting user has a profile but no preferences
- **THEN** the response is 200 with `null`

#### Scenario: Already reacted

- **WHEN** the acting user has liked or disliked the only otherwise fitting user
- **THEN** the response is 200 with `null`

#### Scenario: Not what the acting user wants

- **WHEN** the only other user differs from the acting user's preferences in gender, or age, or city, or dating goal
- **THEN** the response is 200 with `null`

#### Scenario: Not what the candidate wants

- **WHEN** the acting user differs from the only other user's preferences in gender, or age, or city, or dating goal
- **THEN** the response is 200 with `null`

#### Scenario: Any in preferences

- **WHEN** both users' preferences have `null` gender, city and dating goal and each one's age is within the other's
  range
- **THEN** each of them gets the other as a candidate

#### Scenario: Age range boundaries

- **WHEN** the other user's age equals the acting user's `min_age` or `max_age`
- **THEN** the other user is a candidate

#### Scenario: Reported user

- **WHEN** the acting user has an open report against the only fitting user
- **THEN** the response is 200 with that user

### Requirement: Order and response

Candidates SHALL come in random order, one per request. The response SHALL be the candidate's public profile — `id`,
`last_seen_at` and `profile` (with its city) — and SHALL NOT contain Telegram data. When there is no candidate, the
response SHALL be 200 with the body `null`.

#### Scenario: Public profile

- **WHEN** a candidate is returned
- **THEN** the body has `id`, `last_seen_at` and `profile`, and no `telegram` or `username`

#### Scenario: Nobody left

- **WHEN** no user is a candidate for the acting user
- **THEN** the response is 200 with the body `null`

#### Scenario: Random order

- **WHEN** two users are candidates and the acting user asks many times without reacting
- **THEN** both of them are returned
