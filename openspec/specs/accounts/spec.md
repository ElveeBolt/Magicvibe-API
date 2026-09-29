# accounts Specification

## Purpose

Defines how a user account is tied to a Telegram account: registration and refresh on `/start`, permanent account
deletion, the account status, and the acting user's last-online time.

## Requirements

### Requirement: Registration and refresh by Telegram account

`POST /users` SHALL create an account with its Telegram data and return 201 when no account has that Telegram ID. When
an account with that Telegram ID exists and is not banned, it SHALL update the stored Telegram data and return 200 with
the same account. When that account is banned, it SHALL return 403 `USER_BANNED` with `ban: {reason, comment}` and
SHALL NOT change the stored Telegram data.

#### Scenario: New Telegram account

- **WHEN** `POST /users` is called with a Telegram ID no account has
- **THEN** the response is 201 with a new account and its Telegram data

#### Scenario: Returning user

- **WHEN** `POST /users` is called again for an existing, not banned account with a new `first_name`
- **THEN** the response is 200 with the same account ID and the new `first_name`

#### Scenario: Banned user starts the bot again

- **WHEN** `POST /users` is called for a banned account with a new `first_name`
- **THEN** the response is 403 with `code` `USER_BANNED` and the ban's `reason` and `comment`, and the stored
  `first_name` is unchanged

#### Scenario: Start after deletion

- **WHEN** an account is deleted and `POST /users` is then called with the same Telegram ID
- **THEN** the response is 201 with a new account ID

### Requirement: Account deletion

`DELETE /users/{user_id}` SHALL permanently delete the account and all its data: Telegram data, profile, preferences,
reactions given and received, reports filed by and against the user, and bans. It SHALL return 204. Nothing SHALL be
restorable. A banned account SHALL NOT be deleted: the response is 403 `USER_BANNED` and no data changes. An unknown
`user_id` SHALL return 404 `NOT_FOUND`.

#### Scenario: Delete an account

- **WHEN** a not banned user with a profile, preferences, reactions in both directions, reports in both directions and a
  lifted ban is deleted
- **THEN** the response is 204 and none of those rows exist any more

#### Scenario: Other users' data stays

- **WHEN** a user who reacted to another user is deleted
- **THEN** the other user's account and the other user's own reactions to third users remain

#### Scenario: Delete a banned account

- **WHEN** `DELETE /users/{user_id}` is called for a banned user
- **THEN** the response is 403 with `code` `USER_BANNED` and the account and its data remain

#### Scenario: Unknown account

- **WHEN** `DELETE /users/{user_id}` is called with an ID no account has
- **THEN** the response is 404 with `code` `NOT_FOUND`

#### Scenario: No restore

- **WHEN** `POST /users/{user_id}/restore` is called
- **THEN** the response is 404 with `code` `NOT_FOUND`

#### Scenario: Ban and deletion at the same time

- **WHEN** a ban of a user and the deletion of the same user are requested at the same time
- **THEN** either the ban is created and the deletion returns 403 `USER_BANNED`, or the account is deleted and the ban
  returns 404 `NOT_FOUND`; never both a created ban and a deleted account

### Requirement: Account status

An account's `status` SHALL be `active` or `banned` and SHALL change only when a ban is created (to `banned`) or lifted
(to `active`). No endpoint SHALL set it directly. The user response SHALL NOT contain a deletion time.

#### Scenario: Status cannot be set through the API

- **WHEN** `PATCH /users/{user_id}` is called
- **THEN** the response is 405 with `code` `METHOD_NOT_ALLOWED`

#### Scenario: User response fields

- **WHEN** a user is read
- **THEN** the response has `status` `active` or `banned` and no `deleted_at`

### Requirement: Last online time

Every request with an acting user SHALL set that user's `last_seen_at` to the current time when the stored value is
more than one minute old, and SHALL leave it unchanged otherwise.

#### Scenario: Stale last online time

- **WHEN** an acting user whose `last_seen_at` is two minutes old makes a request
- **THEN** their `last_seen_at` becomes the current time

#### Scenario: Recent last online time

- **WHEN** an acting user whose `last_seen_at` is ten seconds old makes a request
- **THEN** their `last_seen_at` is unchanged
