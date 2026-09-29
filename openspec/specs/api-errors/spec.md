# api-errors Specification

## Purpose

Defines how the API reports errors: one JSON body with a stable machine-readable code, the HTTP status of each code,
and the extra fields the bot needs to react without another request.

## Requirements

### Requirement: Error response body

Every error response SHALL have a JSON body with a `code` string in `UPPER_SNAKE_CASE` and a `detail` string in
English. Some codes SHALL add extra top-level fields as listed in this spec. The HTTP status SHALL be the one assigned
to the code. The body SHALL NOT contain stack traces, SQL, database messages or other internals.

#### Scenario: Business error body

- **WHEN** a request is rejected by a business rule
- **THEN** the response body has `code` and `detail`, and the status is the one assigned to that code

#### Scenario: Unknown path

- **WHEN** a request is made to a path the API does not have
- **THEN** the response is 404 with `code` `NOT_FOUND`

#### Scenario: Wrong method

- **WHEN** a request uses an HTTP method a path does not support
- **THEN** the response is 405 with `code` `METHOD_NOT_ALLOWED`

### Requirement: Service token errors

A request with a missing or wrong service token SHALL be rejected with 401 `INVALID_SERVICE_TOKEN` and a
`WWW-Authenticate: Bearer` header, before any other check.

#### Scenario: Missing token

- **WHEN** a request to any endpoint has no `Authorization` header
- **THEN** the response is 401 with `code` `INVALID_SERVICE_TOKEN`

#### Scenario: Wrong token

- **WHEN** a request has a bearer token that is not the service token
- **THEN** the response is 401 with `code` `INVALID_SERVICE_TOKEN`

### Requirement: Validation errors

A request that does not pass the request schema (body, query, path or header) SHALL be rejected, including a
partial update (`PATCH`) body with a field its schema does not define. It SHALL be rejected with 400
`VALIDATION_ERROR` and an `errors` list with one entry per problem. Each entry SHALL have `field` (the dot-separated
path to the value inside its request part, without the part name such as `body` or `query`; empty when the problem
concerns the whole object), `type` (the machine-readable error type, such as `string_too_long`,
`greater_than_equal`, `extra_forbidden`, `missing`) and `message`.

#### Scenario: Field too long

- **WHEN** a request body has a string field longer than its maximum
- **THEN** the response is 400 with `code` `VALIDATION_ERROR` and an `errors` entry with that field's name and
  `type` `string_too_long`

#### Scenario: Unknown field

- **WHEN** a request body has a field the schema does not define
- **THEN** the response is 400 with `code` `VALIDATION_ERROR` and an `errors` entry with that field's name and
  `type` `extra_forbidden`

#### Scenario: Invalid query parameter

- **WHEN** a list endpoint is called with `page_size=101`
- **THEN** the response is 400 with `code` `VALIDATION_ERROR` and an `errors` entry with `field` `page_size`

#### Scenario: Nested field

- **WHEN** a request body has an invalid value in a nested object
- **THEN** the `errors` entry's `field` joins the path with dots, for example `telegram.first_name`

#### Scenario: Unknown field in a partial update

- **WHEN** a `PATCH` body has a field the schema does not define next to a valid one
- **THEN** the response is 400 with `code` `VALIDATION_ERROR`, an `errors` entry with that field's name and `type`
  `extra_forbidden`, and nothing is changed

### Requirement: Unexpected errors

An unhandled error SHALL return 500 `INTERNAL_ERROR` with a `request_id` field equal to the request ID of the request
(the `X-Request-ID` header sent by the client, or the one generated for it). No internals SHALL be exposed.

#### Scenario: Unhandled exception

- **WHEN** an endpoint fails with an unexpected error
- **THEN** the response is 500 with `code` `INTERNAL_ERROR`, a `request_id`, and no error text from the failure

#### Scenario: Request ID from the client

- **WHEN** a request with header `X-Request-ID: abc` fails with an unexpected error
- **THEN** the response `request_id` is `abc`

### Requirement: Database constraint violations

A database constraint violation that reaches the API boundary SHALL be mapped by constraint name: the reaction pair
unique constraint to 409 `ALREADY_REACTED`, the active-ban partial unique index to 409 `BAN_ALREADY_ACTIVE`, and any
other constraint to 409 `CONFLICT`. The database message SHALL be logged and never returned.

#### Scenario: Concurrent second active ban

- **WHEN** creating a ban violates the one-active-ban-per-user index
- **THEN** the response is 409 with `code` `BAN_ALREADY_ACTIVE`

#### Scenario: Other constraint

- **WHEN** a request violates a constraint with no code of its own
- **THEN** the response is 409 with `code` `CONFLICT` and the database message is not in the body

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

### Requirement: Codes of business rejections

Business rejections SHALL use these codes and statuses:

- reacting to or reporting oneself: 400 `SELF_ACTION`;
- reacting to a user already reacted to: 409 `ALREADY_REACTED`;
- creating a ban for a user who already has an active ban: 409 `BAN_ALREADY_ACTIVE`;
- browsing discovery without a profile: 409 `PROFILE_REQUIRED`;
- a resource that does not exist and has no specific code: 404 `NOT_FOUND`;
- a conflict with the current state that has no specific code: 409 `CONFLICT`;
- a business rule rejection that has no specific code: 400 `BAD_REQUEST`.

#### Scenario: Reaction to oneself

- **WHEN** the acting user reacts to their own user ID
- **THEN** the response is 400 with `code` `SELF_ACTION`

#### Scenario: Report of oneself

- **WHEN** the acting user reports their own user ID
- **THEN** the response is 400 with `code` `SELF_ACTION`

#### Scenario: Repeated reaction

- **WHEN** the acting user reacts to a user they have already reacted to
- **THEN** the response is 409 with `code` `ALREADY_REACTED`

#### Scenario: Second active ban

- **WHEN** a ban is created for a user who already has an active ban
- **THEN** the response is 409 with `code` `BAN_ALREADY_ACTIVE`

#### Scenario: Browsing without a profile

- **WHEN** an acting user without a profile asks for the next discovery profile
- **THEN** the response is 409 with `code` `PROFILE_REQUIRED`

#### Scenario: Missing resource

- **WHEN** a ban, report or user is requested by an ID that does not exist
- **THEN** the response is 404 with `code` `NOT_FOUND`
