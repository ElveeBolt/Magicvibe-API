# Spec Delta

## Purpose

Defines how the acting user reacts to another user — like, superlike or dislike, optionally with a message — and when
a reaction completes a match.

## ADDED Requirements

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
