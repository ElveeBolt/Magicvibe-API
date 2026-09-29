# preferences Specification

## Purpose

Defines the discovery preferences — who the user is looking for — which the user sets separately from the profile;
each criterion may be "any".

## Requirements

### Requirement: Setting preferences

`PUT /users/{user_id}/preferences` SHALL create or replace the preferences: `gender` (one gender or `null` for any),
`min_age` and `max_age` (18–100 inclusive, `min_age` not above `max_age`; defaults 18 and 100), `city_id` (an existing
city or `null` for any) and `dating_goal` (one goal or `null` for any). Omitted optional criteria SHALL mean "any".
Values outside the rules SHALL return 400 `VALIDATION_ERROR`; an unknown `city_id` SHALL return 404 `NOT_FOUND`. The
response SHALL carry the city when one is set.

#### Scenario: Any city, any goal

- **WHEN** preferences are put with only `gender`
- **THEN** the response is 200 with `city_id` null, `city` null, `dating_goal` null and ages 18 and 100

#### Scenario: One city and one goal

- **WHEN** preferences are put with an existing `city_id` and `dating_goal` `friendship`
- **THEN** the response is 200 with that city and `dating_goal` `friendship`

#### Scenario: Unknown city

- **WHEN** preferences are put with a `city_id` no city has
- **THEN** the response is 404 with `code` `NOT_FOUND`

#### Scenario: Reversed age range

- **WHEN** preferences are put with `min_age` 30 and `max_age` 20
- **THEN** the response is 400 with `code` `VALIDATION_ERROR`

### Requirement: Changing preferences

`PATCH /users/{user_id}/preferences` SHALL change only the given fields; `gender`, `city_id` and `dating_goal` MAY be
set to `null` for "any". The age range SHALL be checked after merging with the stored values.

#### Scenario: Back to any city

- **WHEN** preferences with a city are patched with `city_id` null
- **THEN** the response is 200 with `city_id` null

#### Scenario: Merged age range

- **WHEN** preferences with `max_age` 25 are patched with `min_age` 30
- **THEN** the response is 400 with `code` `VALIDATION_ERROR`
