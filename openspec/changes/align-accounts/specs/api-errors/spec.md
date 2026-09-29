# Spec Delta

## MODIFIED Requirements

### Requirement: Acting user errors

A request that names an acting user with `X-Telegram-User-Id` SHALL be rejected with 404 `USER_NOT_FOUND` when no
account has that Telegram ID, and with 403 `USER_BANNED` when the account is banned. `USER_BANNED` SHALL carry
`ban: {reason, comment}` of the active ban and no other ban fields.

#### Scenario: Unknown acting user

- **WHEN** a request that needs an acting user has an `X-Telegram-User-Id` no account has
- **THEN** the response is 404 with `code` `USER_NOT_FOUND`

#### Scenario: Banned acting user

- **WHEN** a banned user makes a request that needs an acting user
- **THEN** the response is 403 with `code` `USER_BANNED` and `ban` with exactly `reason` and `comment`

#### Scenario: Deleted acting user

- **WHEN** a request names the Telegram ID of an account that was deleted with `DELETE /users/{user_id}`
- **THEN** the response is 404 with `code` `USER_NOT_FOUND`
