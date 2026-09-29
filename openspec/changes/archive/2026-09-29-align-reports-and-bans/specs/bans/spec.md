# Spec Delta

## Purpose

Defines how an administrator bans a user and lifts the ban: bans have no end date, a user has at most one active ban,
and the account status follows the active ban.

## ADDED Requirements

### Requirement: Creating a ban

`POST /bans` SHALL create a ban for `user_id` with a `reason` and an optional `comment`, return 201, and set the user's
`status` to `banned` in the same transaction. A ban SHALL have no end date: requests and responses SHALL NOT contain
`expires_at`, and a ban SHALL stay active until it is lifted. When the user already has an active ban, the response
SHALL be 409 `BAN_ALREADY_ACTIVE`. An unknown `user_id` SHALL return 404 `NOT_FOUND`.

#### Scenario: Ban a user

- **WHEN** a ban is created for a user without an active ban
- **THEN** the response is 201 with `lifted_at` null and the user's `status` is `banned`

#### Scenario: No end date

- **WHEN** a ban is created with an `expires_at` field
- **THEN** the response is 400 with `code` `VALIDATION_ERROR` and an `errors` entry for `expires_at` with `type`
  `extra_forbidden`

#### Scenario: Second active ban

- **WHEN** a ban is created for a user who already has an active ban
- **THEN** the response is 409 with `code` `BAN_ALREADY_ACTIVE`

#### Scenario: Unknown user

- **WHEN** a ban is created for a user ID no account has
- **THEN** the response is 404 with `code` `NOT_FOUND`

### Requirement: Lifting a ban

`POST /bans/{ban_id}/lift` SHALL set `lifted_at` and the optional `lift_comment`, return 200, and set the user's
`status` to `active` in the same transaction. Lifting a ban that is already lifted SHALL return 409 `CONFLICT`. After a
lift the user MAY be banned again.

#### Scenario: Lift a ban

- **WHEN** an active ban is lifted
- **THEN** the response is 200 with `lifted_at` set and the user's `status` is `active`

#### Scenario: Lift twice

- **WHEN** a lifted ban is lifted again
- **THEN** the response is 409 with `code` `CONFLICT`

#### Scenario: Ban again after a lift

- **WHEN** a user whose ban was lifted is banned again
- **THEN** the response is 201 and the user's `status` is `banned`

### Requirement: A banned user stays banned

A user with an active ban SHALL be rejected with 403 `USER_BANNED` on every request as the acting user, with
`ban: {reason, comment}` of that ban, no matter how much time has passed since the ban was created.

#### Scenario: Old ban

- **WHEN** a user whose ban was created long ago and never lifted makes a request
- **THEN** the response is 403 with `code` `USER_BANNED` and the ban's `reason` and `comment`
