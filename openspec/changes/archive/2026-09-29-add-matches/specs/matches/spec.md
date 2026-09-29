# Spec Delta

## Purpose

Defines what the acting user sees about their matches: the list, and the partner's profile, Telegram contact and like
message that become visible only through a match.

## ADDED Requirements

### Requirement: Match data

A match SHALL be shown to each of its two users with: `user` (the partner's public profile: `id`, `last_seen_at`,
`profile`), `contact` (the partner's Telegram `telegram_id`, `first_name`, `last_name`, `username`), `message` (the
partner's like message to this user, or null), `is_super` (whether the partner's like was a superlike) and
`matched_at`. Telegram data and like messages SHALL NOT appear anywhere outside match data.

#### Scenario: Partner's message after the match

- **WHEN** user A liked user B with a message and they matched
- **THEN** B's match with A has A's message, and A's match with B has B's message or null

#### Scenario: Contact only in matches

- **WHEN** a user is returned by discovery or as a reaction target without a match
- **THEN** the response contains no Telegram data and no like message

### Requirement: Listing matches

`GET /matches` SHALL return the acting user's matches as a paginated list ordered by `matched_at`, newest first by
default. A match whose partner is banned SHALL NOT be listed while the ban lasts, and SHALL be listed again after the
ban is lifted. A match SHALL disappear when either account is deleted.

#### Scenario: Newest first

- **WHEN** the acting user has two matches
- **THEN** the later one comes first

#### Scenario: Banned partner

- **WHEN** the partner of a match is banned
- **THEN** the match is not listed and `total` does not count it

#### Scenario: Ban lifted

- **WHEN** the partner's ban is lifted
- **THEN** the match is listed again

#### Scenario: Partner deleted

- **WHEN** the partner's account is deleted
- **THEN** the match is gone
