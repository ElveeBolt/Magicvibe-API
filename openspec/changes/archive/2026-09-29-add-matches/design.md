# Design

## Context

- `ReactionService.create` inserts with `ON CONFLICT DO NOTHING` on `uq_reaction_pair`, then checks for a reverse like;
  nothing is locked, so two opposite likes in parallel each miss the other's uncommitted row.
- Matches are computed by `ReactionRepository.get_matches` (self-join of reactions); `MatchedUserSchema` adds a
  `username` that `User` does not have.
- `UserRepository.get_for_update` locks one user (`FOR UPDATE OF users`).

## Goals / Non-Goals

**Goals:** a match row for every mutual like, even under concurrency; match data that is the only place with Telegram
data and like messages.

**Non-Goals:** daily limits, superlike plans, "Who liked me" (`add-subscriptions`); unmatch (out of scope in the PRD).

## Decisions

### Lock both users, then decide

`UserRepository.lock_many(ids)` runs `SELECT id, status FROM users WHERE id IN (…) ORDER BY id FOR UPDATE` and returns
`{id: status}`. Ascending order prevents deadlocks between A→B and B→A. After the lock the service: unknown or banned
target → 404; insert the reaction (a repeat → `ALREADY_REACTED`); for a like, read the reverse like and, if there is
one, insert the match. The second of two opposite likes waits on the lock, then sees the first like committed and
creates the match — exactly one, and `uq_match_pair` backs it up.

*Alternative:* insert both ways with `ON CONFLICT` and no lock — rejected: it cannot see an uncommitted reverse like,
which is the whole problem.

### `Match` model and repository

`reaction/models/match.py` (`Match`, table `matches`) with `CheckConstraint(user_a_id < user_b_id, name="ordered_pair")`,
`UniqueConstraint(user_a_id, user_b_id, name="uq_match_pair")`, `Index(None, user_b_id)`; `MatchRepository` in
`reaction/repositories.py`, registered as `uow.match`. The service orders the pair (`min`, `max`).

### Match data from one query

`MatchRepository.get_for_user(user_id, …)` selects `Match`, the partner `User` (joined profile and telegram) and the
partner's `Reaction` to the user, where the partner is the other side of the pair and `User.status = active`
(banned partners are hidden, and reappear on lift because nothing is deleted). `count_for_user` uses the same
conditions. Order by `Match.created_at`, exposed as `matched_at`.

Schemas: `MatchContactSchema` (`telegram_id`, `first_name`, `last_name`, `username`), `MatchReadSchema` (`user:
UserPublicSchema`, `contact`, `message`, `is_super`, `matched_at`). `MatchedUserSchema` is removed.

### Reactions table

`models.md` lists the `(from_user_id, action, is_super, created_at)` index and no separate `from_user_id` index; the
model drops `index=True` on `from_user_id` and adds the composite index. `message_not_empty` is appended by hand to the
generated migration (autogenerate does not see check constraints on existing tables) with a model-test proving it.

## Risks / Trade-offs

- [Existing mutual likes have no match row after the migration] → development data only; noted in the proposal.
- [Two row locks per reaction] → short transactions on two rows; reactions of different pairs do not contend.
