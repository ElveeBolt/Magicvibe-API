# plans Specification

## Purpose

Defines the free and premium plans as the API exposes them: how an administrator grants and ends premium, and which
plan applies to a user at a given moment.

## Requirements

### Requirement: Granting premium

`POST /subscriptions` SHALL grant premium to `user_id` with an optional `comment` and return 201 with the
subscription. The period SHALL start at the moment of granting (a start time in the request SHALL be rejected as an
unknown field) and SHALL last the premium plan's duration of 7 days. `plan` SHALL only accept `premium`. A user SHALL
have at most one current subscription.

#### Scenario: Grant premium

- **WHEN** premium is granted to a user without a current subscription
- **THEN** the response is 201 with `plan` `premium` and `expires_at` exactly 7 days after `starts_at`

#### Scenario: Premium already current

- **WHEN** premium is granted to a user who has a current subscription
- **THEN** the response is 409 with `code` `PREMIUM_ALREADY_ACTIVE`

#### Scenario: Banned user

- **WHEN** premium is granted to a banned user
- **THEN** the response is 409 with `code` `TARGET_USER_BANNED`

#### Scenario: Unknown user

- **WHEN** premium is granted to a user ID no account has
- **THEN** the response is 404 with `code` `NOT_FOUND`

#### Scenario: Free plan cannot be granted

- **WHEN** a subscription is requested with `plan` `free`
- **THEN** the response is 400 with `code` `VALIDATION_ERROR`

#### Scenario: Start time from the request

- **WHEN** a subscription is requested with a `starts_at` field
- **THEN** the response is 400 with `code` `VALIDATION_ERROR` and `type` `extra_forbidden`

#### Scenario: Grant again after the period

- **WHEN** premium is granted to a user whose earlier subscription has ended
- **THEN** the response is 201

#### Scenario: Simultaneous grants

- **WHEN** premium is granted to the same user twice at the same time
- **THEN** exactly one request returns 201, the other 409 `PREMIUM_ALREADY_ACTIVE`, and one subscription exists

### Requirement: Ending premium early

`POST /subscriptions/{subscription_id}/end` SHALL end a current subscription at once by setting `expires_at` to the
current time, and return 200. Ending a subscription that is not current SHALL return 409 `CONFLICT`; an unknown ID,
404 `NOT_FOUND`.

#### Scenario: End early

- **WHEN** a current subscription is ended
- **THEN** the response is 200 and the user's effective plan is `free` right away

#### Scenario: End an ended subscription

- **WHEN** a subscription whose period is over is ended
- **THEN** the response is 409 with `code` `CONFLICT`

### Requirement: Effective plan

`GET /users/{user_id}/plan` SHALL return the plan that applies now: `premium` while a subscription is current
(`starts_at <= now < expires_at`), otherwise `free`. The response SHALL have `code`, `name`, `daily_like_limit`,
`daily_superlike_limit`, `can_see_likers` with the values of the plan table, and `expires_at` of the current
subscription (null on free). An unknown user SHALL return 404 `NOT_FOUND`.

#### Scenario: Free user

- **WHEN** the plan of a user without a current subscription is read
- **THEN** it is `free` with 5 likes, 0 superlikes, `can_see_likers` false and `expires_at` null

#### Scenario: Premium user

- **WHEN** the plan of a user with a current subscription is read
- **THEN** it is `premium` with 20 likes, 5 superlikes, `can_see_likers` true and the subscription's `expires_at`

#### Scenario: At the end of the period

- **WHEN** the plan is read at the subscription's `expires_at`
- **THEN** it is `free`

### Requirement: Listing subscriptions

`GET /subscriptions` SHALL list subscriptions, paginated, newest first by default, optionally filtered by `user_id`;
`GET /subscriptions/{subscription_id}` SHALL return one or 404 `NOT_FOUND`.

#### Scenario: A user's subscriptions

- **WHEN** subscriptions are listed with `user_id`
- **THEN** only that user's subscriptions are returned, newest first
