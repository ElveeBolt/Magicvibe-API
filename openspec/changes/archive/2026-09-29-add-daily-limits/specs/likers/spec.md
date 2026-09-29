# Spec Delta

## Purpose

Defines "Who liked me": the list of users who liked the acting user and are still waiting for their reaction,
available only on plans that include it.

## ADDED Requirements

### Requirement: Who liked me

`GET /likers` SHALL return, as a paginated list, the users who liked or superliked the acting user and whom the acting
user has not reacted to. Banned users SHALL be left out; hidden users SHALL be included. Superlikes SHALL come first
and, within superlikes and within likes, the newest first. Each item SHALL have `user` (the liker's public profile)
and `is_super`, and SHALL NOT contain the like's message or Telegram data. On a plan without "Who liked me" the
response SHALL be 403 `PREMIUM_REQUIRED`.

#### Scenario: Free user

- **WHEN** a free user opens "Who liked me"
- **THEN** the response is 403 with `code` `PREMIUM_REQUIRED`

#### Scenario: Order

- **WHEN** a premium user has an older like, a newer like, an older superlike and a newer superlike
- **THEN** the list is: newer superlike, older superlike, newer like, older like

#### Scenario: Reacted likers leave the list

- **WHEN** the acting user dislikes someone from the list
- **THEN** that user is no longer listed

#### Scenario: Banned and hidden likers

- **WHEN** one liker is banned and another has hidden their profile
- **THEN** the banned one is not listed and the hidden one is

#### Scenario: No message, no contact

- **WHEN** a liker's like has a message
- **THEN** the item has `user` and `is_super` only, without the message or Telegram data

#### Scenario: Like back from the list

- **WHEN** the acting user likes someone from the list
- **THEN** the reaction response has a `match`
