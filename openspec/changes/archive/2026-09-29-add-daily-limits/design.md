# Design

## Context

- `ReactionService.create` locks both users with `lock_many`, rejects a banned target, inserts with
  `ON CONFLICT DO NOTHING`, and creates the match.
- `SubscriptionService.get_effective_plan(user_id)` returns `(Plan, Subscription | None)` inside the caller's unit of
  work.
- The index `(from_user_id, action, is_super, created_at)` exists.
- `ServiceError` carries `headers`, and the handler passes them on.
- In tests `now()` is fixed for the whole transaction; time must never pass for real (`testing.md` → Time).

## Goals / Non-Goals

**Goals:** limits that hold under concurrency; day boundaries correct across daylight saving time; tests at the
midnight boundary without waiting.

**Non-Goals:** telling users how many likes are left (out of scope in the PRD).

## Decisions

### Day bounds from the database

`ReactionRepository.day_bounds(at)` runs one `SELECT` returning, for the instant `at` (default `now()`):
`day_start = (date_trunc('day', at AT TIME ZONE 'Europe/Kyiv')) AT TIME ZONE 'Europe/Kyiv'` and
`next_reset = (date_trunc('day', at AT TIME ZONE 'Europe/Kyiv') + interval '1 day') AT TIME ZONE 'Europe/Kyiv'`, plus
`at` itself. PostgreSQL's time zone database handles the 23- and 25-hour days. Tests call it with explicit instants
around midnight and on the DST days. *Alternative:* Python `zoneinfo` — rejected: the Alpine image has no system time
zone data and the project has no `tzdata` dependency; the database clock is also the one `created_at` uses.

### Order of checks in `POST /reactions`

1. self → `SELF_ACTION`; 2. lock both users; banned or unknown target → `NOT_FOUND`; 3. the pair already reacted →
`ALREADY_REACTED` (so a repeat is not reported as a limit); 4. like/superlike only: effective plan; superlike with
limit 0 → `PREMIUM_REQUIRED`; count since `day_start` with the index (`action = like`, `is_super` as requested) and
compare with the plan's limit → `DAILY_LIMIT_REACHED`; 5. insert, match.

The count runs after the acting user's row lock, so a second reaction of the same user waits for the first to commit
and then counts it (each statement sees committed rows). Unlike the grant race in `add-subscriptions`, the count's
lower bound is midnight, not `now()`, so a waiting transaction still sees the other's row.

### The 429 response

`DailyLimitError` is not a new class: `ServiceError` with `code=DAILY_LIMIT_REACHED`, `extra={"limit_type": …,
"resets_at": …}` and `headers={"Retry-After": str(ceil(seconds))}`. `resets_at` is serialized as ISO 8601 UTC.

### "Who liked me"

`ReactionRepository.get_likers(user_id, …)` selects the liker `User` and their like to the user where no reaction from
the user to the liker exists and the liker is `active`; order `is_super DESC, created_at DESC`. The route `GET
/likers` sits in the reaction router (like `/matches`) and checks `plan.can_see_likers` first. Item schema
`LikerReadSchema`: `user: UserPublicSchema`, `is_super`.

## Risks / Trade-offs

- [`resets_at` depends on the database server's time zone data] → PostgreSQL ships its own; tested on the DST dates.
- [A user near the limit sending many likes in parallel waits on their own row lock] → one user's requests only.
