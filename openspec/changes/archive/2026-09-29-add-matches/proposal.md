# Proposal

## Why

[PRD → Reactions and matches](../../../docs/prd.md#67-reactions-and-matches) and
[Data model → `reaction` domain](../../../docs/architecture/models.md#reaction-domain) store a match as its own row,
created in the same transaction as the like that completes the pair, after locking both users; hide a match while one
of its users is banned; give both users each other's Telegram contact; and show a like's message to its recipient only
after a match. The code has no `matches` table (matches are derived from reaction pairs on every read), no locking —
two opposite likes at the same time can both miss each other and create no match at all —, lets users react to banned
users, lists banned partners, and builds the match with a `username` field that `User` does not have. `reactions`
also lacks the `message_not_empty` check and the daily-limit index, and has an index `models.md` does not list.

## What Changes

- New `matches` table (`user_a_id` < `user_b_id`, `uq_match_pair`, `ordered_pair`, index on `user_b_id`,
  `ON DELETE CASCADE`).
- `POST /reactions` locks both users (`SELECT … FOR UPDATE`, ascending ID), rejects a banned target as 404 `NOT_FOUND`
  (banned users are hidden from others), inserts the reaction, and for a like whose reverse like exists inserts the
  match in the same transaction. Two opposite likes at the same time create exactly one match.
- Match data (in `POST /reactions` and `GET /matches`): the partner's public profile, their Telegram contact
  (`telegram_id`, `first_name`, `last_name`, `username`), their like message to the acting user (visible only here),
  `is_super` of their like, and `matched_at` (the match row's `created_at`).
- `GET /matches` reads the `matches` table, newest first by default, and leaves out matches whose partner is banned.
- `reactions`: `message_not_empty` check (appended by hand to the generated migration, as the migrations rule allows),
  the `(from_user_id, action, is_super, created_at)` index; the separate `from_user_id` index goes.
- Existing mutual likes get no `matches` row: migrations never change data, and no database outside development holds
  reactions yet.
- Daily limits and superlike plans come with `add-subscriptions`.

## Capabilities

### New Capabilities

- `reactions`: reacting to a user (like, superlike, dislike, message), what is rejected, and the match it may create.
- `matches`: the list of the acting user's matches and what one match shows.

### Modified Capabilities

None.

## Impact

- Code: `reaction` (new `Match` model in `models/match.py`, `MatchRepository`, service, schemas),
  `user/repositories.py` (lock several users), `uow.py` (`match` repository), `alembic/env.py`, a migration.
- API: the match object changes shape (`user` + `contact` + `message` + `is_super` + `matched_at`); a banned target
  returns 404.
- Docs: none — `prd.md` and `models.md` already describe the target.
