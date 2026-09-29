# Proposal

## Why

[Plans → Daily limits](../../../docs/plans.md#daily-limits) limits likes and superlikes per day by the effective plan,
resetting at midnight Europe/Kyiv; [Errors → Daily limit](../../../docs/architecture/errors.md#daily-limit) answers a
used-up limit with 429 `DAILY_LIMIT_REACHED`, `limit_type`, `resets_at` and `Retry-After`, and a superlike on a plan
without superlikes with 403 `PREMIUM_REQUIRED`. [PRD → Plans and premium](../../../docs/prd.md#68-plans-and-premium)
defines "Who liked me" for plans that include it. None of this is enforced or exists: every user can like without
limit and superlike on the free plan.

## What Changes

- `POST /reactions`: before a like or superlike, the effective plan (from `add-subscriptions`) and the acting user's
  likes and superlikes since the last reset at midnight Europe/Kyiv are checked:
  - a superlike on a plan whose superlike limit is 0 → 403 `PREMIUM_REQUIRED`;
  - a used-up limit → 429 `DAILY_LIMIT_REACHED` with `limit_type` (`like` / `superlike`), `resets_at` (next midnight
    Europe/Kyiv, in UTC) and a `Retry-After` header with the seconds until then;
  - a superlike counts only toward the superlike limit; dislikes are never limited.
  - The check runs after the acting user's row is locked (already done for matches), so parallel likes cannot exceed
    the limit; a repeated reaction is still 409 `ALREADY_REACTED` even at the limit.
- New `GET /likers` ("Who liked me"): users who liked or superliked the acting user and whom the acting user has not
  reacted to, banned users excluded, hidden users included; superlikes first, newest first within each; each item is
  the liker's public profile and `is_super`, never the message. Plans without "Who liked me" → 403
  `PREMIUM_REQUIRED`. Paginated.
- Day boundaries are computed by the database (`AT TIME ZONE 'Europe/Kyiv'`), so daylight saving time is handled and
  the API needs no time zone data of its own.

## Capabilities

### New Capabilities

- `likers`: the "Who liked me" list.

### Modified Capabilities

- `reactions`: a new requirement for daily limits and the superlike plan check.

## Impact

- Code: `reaction` (repository: counting and day bounds, likers query; service; router `/likers`; schemas),
  `subscription` (reused `get_effective_plan`), `reaction/constants.py` (`LIMIT_TIME_ZONE = "Europe/Kyiv"`).
- API: `POST /reactions` can return 403 and 429; new `GET /likers`.
- No model or migration changes (the daily-limit index exists since `add-matches`).
- Docs: none — `plans.md`, `errors.md` and `prd.md` already describe the target.
