# Proposal

## Why

[Plans](../../../docs/plans.md) defines a free and a premium plan, premium granted by an administrator for 7 days from
the moment of granting, at most one current premium period per user, never for a banned user, and endable early;
[Plan constants](../../../docs/architecture/plan_constants.md) and
[Data model → `subscription` domain](../../../docs/architecture/models.md#subscription-domain) define how. None of it
exists. The daily limits and "Who liked me" (next change, `add-daily-limits`) depend on the effective plan this
change introduces.

## What Changes

- New `subscription` domain: `PlanCode` (`free`, `premium`), the plan classes and `PLANS` in
  `subscription/constants.py` exactly as `plan_constants.md` shows them, and the `subscriptions` table with
  `expires_after_start`, `paid_plan_only` and the `(user_id, expires_at)` index.
- `POST /subscriptions` (administrator): grants premium to `user_id` with an optional `comment`. `starts_at` is the
  database's `now()` (never taken from the API) and `expires_at` is `starts_at` + the plan's `duration_days`. Unknown
  user → 404 `NOT_FOUND`; banned user → 409 `TARGET_USER_BANNED`; a current subscription exists → 409
  `PREMIUM_ALREADY_ACTIVE`. The user row is locked, so two simultaneous grants give one subscription.
- `POST /subscriptions/{subscription_id}/end`: ends a current subscription now (`expires_at = now()`); one that is not
  current → 409 `CONFLICT`.
- `GET /subscriptions` (paginated, filter by `user_id`) and `GET /subscriptions/{subscription_id}`.
- `GET /users/{user_id}/plan`: the effective plan (premium during a current subscription, otherwise free) with its
  limits, `can_see_likers` and `expires_at` of the current subscription (null on free).
- Not here: enforcing daily limits, `PREMIUM_REQUIRED`, "Who liked me" (`add-daily-limits`).

## Capabilities

### New Capabilities

- `plans`: granting and ending premium, listing subscriptions, and a user's effective plan.

### Modified Capabilities

None.

## Impact

- Code: new `src/magicvibe/subscription/`, `user/repositories.py` untouched (it already has `get_for_update`),
  `uow.py`, `router.py`, `alembic/env.py`, a migration (new table, so autogenerate covers the checks).
- Tests: `tests/subscription/`, a factory for subscriptions.
- Docs: none — `plans.md`, `plan_constants.md`, `models.md` and `errors.md` already describe the target.
