# Spec Delta

## Purpose

Defines the user's profile — what other users see — with its required and optional fields and the rules each value
must meet.

## ADDED Requirements

### Requirement: Creating or replacing the profile

`PUT /users/{user_id}/profile` SHALL create or replace the profile with the required `name` (1–64 characters),
`birth_date` (age 18–100 inclusive), `gender` (`male`, `female`, `other`), `city_id` (an existing city) and
`dating_goal` (`relationship`, `friendship`, `casual`, `chatting`), and the optional `bio` (1–500 characters) and
`is_visible` (default `true`). It SHALL NOT create preferences. A missing required field or a value outside the rules
SHALL return 400 `VALIDATION_ERROR`; an unknown `city_id` SHALL return 404 `NOT_FOUND`.

#### Scenario: Complete profile

- **WHEN** a profile is put with all required fields and no bio
- **THEN** the response is 200 with those fields, `bio` null, `is_visible` true, `age` and the city

#### Scenario: Missing dating goal

- **WHEN** a profile is put without `dating_goal`
- **THEN** the response is 400 with `code` `VALIDATION_ERROR` and an `errors` entry for `dating_goal` with `type`
  `missing`

#### Scenario: Unknown dating goal

- **WHEN** a profile is put with `dating_goal` `marriage`
- **THEN** the response is 400 with `code` `VALIDATION_ERROR` and an `errors` entry for `dating_goal`

#### Scenario: Unknown city

- **WHEN** a profile is put with a `city_id` no city has
- **THEN** the response is 404 with `code` `NOT_FOUND`

#### Scenario: Empty bio

- **WHEN** a profile is put with `bio` that is empty or only spaces
- **THEN** the response is 400 with `code` `VALIDATION_ERROR` and an `errors` entry for `bio`

#### Scenario: Bio too long

- **WHEN** a profile is put with a 501-character `bio`
- **THEN** the response is 400 with an `errors` entry for `bio` with `type` `string_too_long`

#### Scenario: No preferences as a side effect

- **WHEN** a user without preferences puts a profile
- **THEN** reading their preferences returns 404 with `code` `NOT_FOUND`

### Requirement: Changing the profile

`PATCH /users/{user_id}/profile` SHALL change only the given fields, under the same rules as creation. `bio` MAY be set
to `null` to remove it; the required fields SHALL NOT be set to `null`. An unknown `city_id` SHALL return 404
`NOT_FOUND`.

#### Scenario: Change the city

- **WHEN** the profile is patched with another existing `city_id`
- **THEN** the response is 200 with the new city and the other fields unchanged

#### Scenario: Remove the bio

- **WHEN** the profile is patched with `bio` null
- **THEN** the response is 200 with `bio` null

#### Scenario: Required field set to null

- **WHEN** the profile is patched with `dating_goal` null
- **THEN** the response is 400 with `code` `VALIDATION_ERROR`
